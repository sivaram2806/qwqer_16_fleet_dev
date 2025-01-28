# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import formatLang


class AccountMoveExtend(models.Model):
    """
       This model account.move is inherited to make modification for ftl trip summary and work order
       """
    _inherit = 'account.move'

    work_order_id = fields.Many2one('work.order', string='Work Order No.', copy=False)
    work_order_ids = fields.Many2many(comodel_name='work.order', relation="account_move_work_order", column1="work_order_id",
                                column2='move_id')
    work_order_amount = fields.Float(string='Work Order Amount')
    work_order_shipping_address = fields.Text(string='Work Order Shipping Address')
    vehicle_ftl_customer_consolidate_id = fields.Many2one('trip.summary.ftl', string='Ftl Consolidated No.',
                                                          copy=False)
    is_ftl = fields.Boolean(string="Is Ftl", compute="_compute_is_ftl")

    def action_post(self):
        """extend to change the trip_summary_ftl/ftl_customer_consolidate state to post/"""
        for rec in self:
            res = super(AccountMoveExtend, self).action_post()
            if rec.vehicle_ftl_customer_consolidate_id:
                rec.vehicle_ftl_customer_consolidate_id.state = 'posted'
            return res

    def button_draft(self):
        for rec in self:
            if rec.vehicle_ftl_customer_consolidate_id:
                # restrict Reset to draft is if invoice state is cancelled
                if rec.state == 'cancel':
                    raise UserError(
                        _("Reset to draft is restricted in cancelled consolidated invoice. Please create a new "
                          "consolidated invoice"))
                else:
                    # change the status of consolidate to draft when invoice id reset to draft
                    rec.vehicle_ftl_customer_consolidate_id.state = 'draft'
            return super(AccountMoveExtend, self).button_draft()

    def button_cancel(self):
        """extend to resetting the batch_trip_ftl and trip_summary_ftl on cancelling invoice"""
        res = super(AccountMoveExtend, self).button_cancel()
        for rec in self:
            if rec.vehicle_ftl_customer_consolidate_id:
                rec.vehicle_ftl_customer_consolidate_id.state = 'cancelled'
            daily_trip = self.env['batch.trip.ftl'].search(
                [('trip_summary_ftl_id', '=', rec.vehicle_ftl_customer_consolidate_id.id)])
            if daily_trip:
                daily_trip.write({'invoice_state': 'to_invoice', 'trip_summary_ftl_id': False})
        return res

    def unlink(self):
        """extend to resetting the trip_summary_ftl on deleting invoice"""
        for rec in self:
            if rec.vehicle_ftl_customer_consolidate_id:
                if rec.state != 'cancel':
                    rec.vehicle_ftl_customer_consolidate_id.state = 'new'
            return super(AccountMoveExtend, self).unlink()

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state')
    def _compute_amount(self):
        """extend to setting consolidate to paid if invoice is paid"""
        res = super(AccountMoveExtend, self)._compute_amount()
        for rec in self:
            if rec.vehicle_ftl_customer_consolidate_id:
                if (rec.vehicle_ftl_customer_consolidate_id.invoice_id.payment_state == "paid"
                        and rec.vehicle_ftl_customer_consolidate_id.invoice_id.state == "posted"):
                    rec.vehicle_ftl_customer_consolidate_id.state = "paid"

        return res

    @api.depends('segment_id')
    def _compute_is_ftl(self):
        """function to identify is the account.move record from ftl"""
        for rec in self:
            if rec.segment_id.is_ftl:
                rec.is_ftl = True
            else:
                rec.is_ftl = False

    @api.onchange('work_order_ids', 'work_order_id')
    def onchange_work_order(self):
        """ setting work_order_billing_address,work_order_shipping_address,work_order_amount on change work_order_id"""
        for rec in self:
            if rec.move_type == "out_invoice" and rec.work_order_ids:
                rec.work_order_amount = sum(rec.work_order_ids.mapped("total_amount"))
                rec.work_order_shipping_address = rec.work_order_ids[0].shipping_address
            elif rec.move_type == "in_invoice" and rec.work_order_id:
                rec.work_order_amount = rec.work_order_id.total_amount
                rec.work_order_shipping_address = rec.work_order_id.shipping_address
            else:
                rec.work_order_amount = False
                rec.work_order_shipping_address = False

    @api.onchange('invoice_line_ids')
    def _onchange_quick_edit_line_ids(self):
        res = super(AccountMoveExtend, self)._onchange_quick_edit_line_ids()
        if self.region_id.analytic_account_id:
            analytic_account_id = self.region_id.analytic_account_id.id
            for rec in self.invoice_line_ids:
                rec.analytic_distribution = {str(analytic_account_id): 100.0}
        return res

    # To show the TDS amount separately from the total amount

    def _compute_payments_widget_to_reconcile_info(self):
        res = super(AccountMoveExtend, self)._compute_payments_widget_to_reconcile_info()
        for move in self:
            if move.invoice_outstanding_credits_debits_widget:
                payments_widget_vals = move.invoice_outstanding_credits_debits_widget
                widget_content = []
                for item in payments_widget_vals.get('content', []):
                    line_id = item.get('id')
                    line = self.env['account.move.line'].browse(line_id)
                    tds_amount = 0.0
                    if line.payment_id:
                        tds_amount = line.payment_id.tds_amount or 0.0
                    item['tds_amount'] = tds_amount
                    widget_content.append(item)
                payments_widget_vals['content'] = widget_content
                move.invoice_outstanding_credits_debits_widget = payments_widget_vals
        return res

    @api.depends('move_type', 'line_ids.amount_residual')
    def _compute_payments_widget_reconciled_info(self):
        """overridden for adding TDS amount"""
        for move in self:
            payments_widget_vals = {'title': _('Less Payment'), 'outstanding': False, 'content': []}

            if move.state == 'posted' and move.is_invoice(include_receipts=True):
                reconciled_vals = []
                reconciled_partials = move._get_all_reconciled_invoice_partials()
                for reconciled_partial in reconciled_partials:
                    counterpart_line = reconciled_partial['aml']
                    if counterpart_line.move_id.ref:
                        reconciliation_ref = '%s (%s)' % (counterpart_line.move_id.name, counterpart_line.move_id.ref)
                    else:
                        reconciliation_ref = counterpart_line.move_id.name
                    if counterpart_line.amount_currency and counterpart_line.currency_id != counterpart_line.company_id.currency_id:
                        foreign_currency = counterpart_line.currency_id
                    else:
                        foreign_currency = False

                    reconciled_vals.append({
                        'name': counterpart_line.name,
                        'journal_name': counterpart_line.journal_id.name,
                        'amount': reconciled_partial['amount'],
                        'currency_id': move.company_id.currency_id.id if reconciled_partial['is_exchange'] else
                        reconciled_partial['currency'].id,
                        'date': counterpart_line.date,
                        'partial_id': reconciled_partial['partial_id'],
                        'account_payment_id': counterpart_line.payment_id.id,
                        'tds_amount': formatLang(self.env, abs(counterpart_line.payment_id.tds_amount),
                                                              currency_obj=counterpart_line.company_id.currency_id),
                        'payment_method_name': counterpart_line.payment_id.payment_method_line_id.name,
                        'move_id': counterpart_line.move_id.id,
                        'ref': reconciliation_ref,
                        # these are necessary for the views to change depending on the values
                        'is_exchange': reconciled_partial['is_exchange'],
                        'amount_company_currency': formatLang(self.env, abs(counterpart_line.balance),
                                                              currency_obj=counterpart_line.company_id.currency_id),
                        'amount_foreign_currency': foreign_currency and formatLang(self.env,
                                                                                   abs(counterpart_line.amount_currency),
                                                                                   currency_obj=foreign_currency)
                    })
                payments_widget_vals['content'] = reconciled_vals

            if payments_widget_vals['content']:
                move.invoice_payments_widget = payments_widget_vals
            else:
                move.invoice_payments_widget = False
