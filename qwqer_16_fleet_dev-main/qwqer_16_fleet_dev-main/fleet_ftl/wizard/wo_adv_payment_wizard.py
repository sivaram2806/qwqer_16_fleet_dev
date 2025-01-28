# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime


class WOAdvPaymentWiz(models.TransientModel):
    """
    Wizard to get and payment information and create a payment in account.payment
    """
    _name = 'wo.adv.payment.wizard'
    
    @api.model
    def default_get(self, field_list):
        """Function to get values for payment method, cashfree journal"""
        res = super().default_get(field_list)
        payment_method_id = self.env['account.payment.method'].search([('payment_type', '=', 'outbound'),
                                                                       ('code', '=', 'manual')], limit=1)
        cashfree_journal = self.env['account.journal'].search([('is_cashfree', '=', True)], limit=1)
        active_ids = self.env.context.get('active_ids')
        wo = self.env['work.order'].browse(active_ids)
        amount = 0.0
        if wo.adv_payment_type == 'percentage':
            amount = (wo.vendor_cost / 100) * int(wo.adv_payment_percentage)

        # show_tds checking
        show_tds = self.env['account.move'].check_turnover(wo.vendor_id.id,
                                                           wo.vendor_id.tax_tds_id.payment_excess,
                                                           amount) if wo.vendor_id.tds_threshold_check else False
        def_fields = {'payment_method_id': payment_method_id.id,
                      'partner_id': wo.vendor_id,
                      'comments': wo.name,
                      'journal_id': cashfree_journal.id,
                      'amount': amount,
                      'show_tds': show_tds,
                      'tax_tds_id': wo.vendor_id.tax_tds_id.id if wo.vendor_id.tds_threshold_check else False,
                      'tds_amount': (amount * (wo.vendor_id.tax_tds_id.amount/100)) ,
                      'work_order_amount': wo.vendor_cost}
        res.update(def_fields)
        return res
    
    partner_id = fields.Many2one('res.partner', string='Vendor', domain= lambda self:  [("company_id", "=", self.env.company.id)])
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method', required=True)
    comments = fields.Char(string='Comments')
    amount = fields.Float(string="Amount")
    date = fields.Date(string='Date',  default=fields.Date.today())
    journal_id = fields.Many2one('account.journal', string='Journal')
    payment_through = fields.Selection([("online", "Online"), ("bank", "Bank")])
    work_order_amount = fields.Float(string="Work Order Amount")
    is_amount_greater = fields.Boolean(default=False)
    show_tds = fields.Boolean(string="Show TDS")
    tax_tds_id = fields.Many2one('account.tax', string="TDS", domain=[('is_tds', '=', True)])
    tds_amount = fields.Monetary(string="TDS Amount", currency_field='currency_id', store=True)

    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency',
        compute='_compute_currency_id', store=True, readonly=False, precompute=True,
        help="The payment's currency.")

    @api.depends('journal_id')
    def _compute_currency_id(self):
        for wo_pay in self:
            wo_pay.currency_id = wo_pay.journal_id.currency_id or wo_pay.journal_id.company_id.currency_id

    @api.onchange('payment_through')
    def onchange_payment_through(self):
        """Function to change values based on payment through field value"""
        for rec in self:
            if rec.payment_through == 'online':
                cashfree_journal = self.env['account.journal'].search([('is_cashfree', '=', True)], limit=1)
                if cashfree_journal:
                    rec.journal_id = cashfree_journal.id
                else:
                    rec.journal_id = False
            elif rec.payment_through == 'bank':
                bank_journal = self.env['account.journal'].search([('is_bank_journal', '=', True)], limit=1)
                if bank_journal:
                    rec.journal_id = bank_journal.id
                else:
                    rec.journal_id = False
            else:
                rec.journal_id = False
                
    @api.onchange('amount')
    def onchange_amount(self):
        """Function to change values based on payment through field value"""
        for rec in self:
            if rec.amount > rec.work_order_amount:
                rec.is_amount_greater = True
            else:
                rec.is_amount_greater = False
            if rec.partner_id.tds_threshold_check:
                rec.show_tds = rec.env['account.move'].check_turnover(rec.partner_id.id,
                                                                   rec.partner_id.tax_tds_id.payment_excess,
                                                                   rec.amount)
                if rec.show_tds:
                    rec.tds_amount = (rec.amount * (rec.partner_id.tax_tds_id.amount / 100))

    def action_advance_payment(self):
        """Function to create payment record in account.payment"""
        for rec in self:
            if rec.amount == 0:
                raise ValidationError(_("Not allowed to create payment with zero amount."))
            active_ids = self.env.context.get('active_ids')
            work_order = self.env['work.order'].browse(active_ids)
            total_advance_amount = sum(work_order.payment_ids.mapped("amount"))
            if (total_advance_amount + rec.amount) > work_order.vendor_cost:
                raise ValidationError(
                    "The total payment will exceed the vendor's cost after this transaction. "
                    f"Please review before proceeding. \nTotal paid so far: {total_advance_amount}")
            payment = self.env['account.payment'].create({
                'payment_type': 'outbound',
                'partner_type': 'supplier',
                'partner_id': rec.partner_id.id,
                'journal_id': rec.journal_id.id,
                'amount': rec.amount,
                'date': rec.date,
                'payment_method_id': rec.payment_method_id.id,
                'ref': work_order.name,
                'work_order_id': work_order.id,
                'state': 'draft',
                'tax_tds_id': self.tax_tds_id.id,
                'tds_amount': self.tds_amount
                })
            payment.onchange_work_order()
            self.action_post_payment(payment)
            if payment.journal_id.is_cashfree:
                line_list = [(0, 0, {'transaction_date': fields.datetime.now(),
                                     'payment_state': 'initiate'})]
                payment.write({'is_cashfree': True})
                payment.write({'is_cashfree': True, 'cashfree_payment_line_ids': line_list})
                payment.action_cashfree_payment()
            form_view = self.env.ref('account.view_account_payment_form')
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'res_id': payment.id,
                'view_mode': 'form',
                'view_id': form_view.id,
                'context': {'create': False},
                'target': 'current',
                }

    def action_post_payment(self, payment_obj):
        if payment_obj:
            payment_obj.action_post()