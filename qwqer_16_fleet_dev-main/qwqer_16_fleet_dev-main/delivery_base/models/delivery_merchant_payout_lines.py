# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime
import pytz
import base64
from dateutil import tz


class DeliveryMerchantPayoutLines(models.Model):
    _name = 'delivery.merchant.payout.lines'
    _description = 'Payout Lines'
    _rec_name = 'customer_id'

    @api.model
    def _default_delivery_service_type(self):
        service_type = self.env['partner.service.type'].search(
            [('is_delivery_service', '=', True), ('company_id', '=', self.env.company.id)], limit=1)
        return service_type.id if service_type else False

    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    payment_state = fields.Selection(selection=[
        ('initiate', 'Initiated'),
        ('pending', 'Pending'),
        ('fail', 'Failed'),
        ('success', 'Success'), ], string='Status')
    invoice_id = fields.Many2one(comodel_name='account.move', string="Invoices")
    payment_id = fields.Many2one(comodel_name='account.payment', string="Payment")
    line_ids = fields.Many2many(comodel_name='account.move.line', relation='move_payout_lines_rel',
                                column1='payout_lines_id', column2='acc_lines_id',
                                string='Transactions')
    customer_id = fields.Many2one('res.partner')
    payment_journal_id = fields.Many2one(comodel_name='account.move', string="Payment Journal Entry")
    payout_id = fields.Many2one(comodel_name='delivery.merchant.payout', string="Payout")
    region_id = fields.Many2one(related='payout_id.region_id', string='region', store=True)
    total_pay = fields.Float(string='Total Amount(A)', digits='Product Price', compute='compute_total_amount',
                             store=True)
    balance_amt = fields.Float(string='Deduction(B)', digits='Product Price')
    service_charge = fields.Float(string='Service Charge(C)', digits='Product Price', store=True)
    taxes = fields.Float(string='Taxes(D)', digits='Product Price', store=True)
    final_pay = fields.Float(string='Total Payout (A-B-C-D)', compute='get_total_payout', store=True,
                             digits='Product Price')
    cashfree_ref = fields.Char(string="Payment Gateway Ref#", copy=False)
    utr_ref = fields.Char(string="UTR", copy=False)
    transfer_date = fields.Datetime("Transaction Date")
    processed_date = fields.Datetime("Processed Date")
    transfer_ref = fields.Char(string="Transfer ID")
    remarks = fields.Text(string="Remarks")
    re_initiated = fields.Selection(selection=[
        ('yes', 'Yes'),
        ('no', 'No'), ], string='Re-initiate', default='no')
    is_mail_sent = fields.Boolean(string="Is Delivery Mail Sent", default=False)
    status_description = fields.Text(string="Status Description")
    delivery_service_type_id = fields.Many2one(comodel_name='partner.service.type',
                                            default=lambda self: self._default_delivery_service_type())

    @api.model
    def create(self, vals):
        company_id = self.env.company.id
        sequence = self.env['ir.sequence'].search(
            [('company_id', '=', company_id), ('code', '=', 'delivery.merchant.payout.line.seq')])
        if not sequence:
            sequence = self.env['ir.sequence'].search([('code', '=', 'delivery.merchant.payout.line.seq')], limit=1)
            new_sequence = sequence.sudo().copy()
            new_sequence.company_id = company_id
            vals['transfer_ref'] = new_sequence.next_by_id()
        else:
            vals['transfer_ref'] = self.env['ir.sequence'].next_by_code('delivery.merchant.payout.line.seq')
        return super(DeliveryMerchantPayoutLines, self).create(vals)

    def unlink(self):
        for rec in self:
            if rec.line_ids:
                rec.line_ids.write({'merchant_payout_id': False})
        return super(DeliveryMerchantPayoutLines, self).unlink()

    @api.onchange('total_pay', 'balance_amt')
    def onchange_service_chrg(self):
        for rec in self:
            is_credit_customer = rec.customer_id.payment_mode_ids.filtered(
                lambda s: s.is_credit_payment == True) or False
            if rec.total_pay and is_credit_customer and rec.customer_id.merchant_amount_collection == 'yes':
                charge = (rec.total_pay * rec.customer_id.collection_charges) / 100
                rec.service_charge = charge

    @api.onchange('line_ids')
    def onchange_line(self):
        for rec in self:
            if rec.line_ids:
                res = self.env['account.move.line'].sudo().search([('partner_id', '=', rec.customer_id.id), (
                    'merchant_payout_id', '=', rec._origin.payout_id.id)]).ids
                if res:
                    res1 = list(set(rec.line_ids.ids).symmetric_difference(set(res)))
                    if res1:
                        self.env['account.move.line'].sudo().browse(res1).write(({
                            'merchant_payout_id': False
                        }))

    @api.depends('line_ids')
    def compute_total_amount(self):
        for rec in self:
            rec.total_pay = sum(rec.line_ids.mapped('credit'))

    @api.onchange('total_pay', 'balance_amt', 'service_charge')
    def onchange_taxes(self):
        for rec in self:
            tax_amt = 0
            for ele in rec.customer_id.b2b_invoice_tax_ids:
                tax_val = ele.with_context(round=True).compute_all(rec.service_charge)
                tax_list = tax_val.get('taxes', [])
                if tax_list:
                    for data in tax_list:
                        tax_amt += round(data.get('amount', 0.0), 2)
            rec.taxes = tax_amt

    @api.depends('total_pay', 'balance_amt', 'service_charge', 'taxes')
    def get_total_payout(self):
        for rec in self:
            rec.final_pay = rec.total_pay - rec.balance_amt - rec.service_charge - rec.taxes

    def unrec_entries(self):
        for rec in self:
            mv_list = rec.line_ids and rec.line_ids.ids or []
            for mv_line in rec.payment_journal_id.line_ids:
                if mv_line.debit > 0.0:
                    mv_list.append(mv_line.id)
            move_line_ids = self.env['account.move.line'].browse(mv_list)
            move_line_ids.remove_move_reconcile()
            rec.payment_journal_id.button_cancel()
            for line in rec.line_ids:
                line.merchant_payout_id = False

    def action_shop_xls_print(self):
        for rec in self:
            data = {
                'ids': self.env.context.get('active_ids', []),
                'model': 'delivery.merchant.payout.lines',
            }
            return self.env.ref(
                'delivery_base.delivery_merchant_payoutline_formview_xlsx_report').report_action(self,
                                                                                                           data=data)

    def mail_sent_template(self):
        attachments = []
        if self.invoice_id:
            try:
                pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf('account.account_invoices',
                                                                                res_ids=self.invoice_id.id)
            except Exception as e:
                raise UserError(f"Error generating invoice PDF: {str(e)}")
            attachment_1 = self.env['ir.attachment'].create({
                'name': f'invoice_{self.customer_id.name}.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
            })
            attachments.append((4, attachment_1.id))
        try:
            report_id = self.env.ref('delivery_base.delivery_merchant_payoutline_formview_xlsx_report')
            xlsx_content = self.env['ir.actions.report'].sudo()._render_xlsx(report_id.id, [self.id], None)
        except Exception as e:
            raise UserError(f"Error generating XLSX report: {str(e)}")

        attachment_2 = self.env['ir.attachment'].create({
            'name': f'payout_report_{self.customer_id.name}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(xlsx_content[0]),
            'res_model': self._name,
            'res_id': self.id,
        })
        attachments.append((4, attachment_2.id))
        local_transfer_date = False
        if self.transfer_date:
            user_zone = tz.gettz(self.env.user.tz or pytz.utc)
            utc = datetime.strptime(str(self.transfer_date), '%Y-%m-%d %H:%M:%S')
            local_transfer_date = utc.astimezone(user_zone)
            local_transfer_date = local_transfer_date.strftime('%d-%m-%Y')
        mail_template_id = self.env.ref('delivery_base.mail_template_delivery_merchant_payout')
        # template = self.env['mail.template'].browse(mail_template_id)
        ctx = {
            'default_model': 'delivery.merchant.payout.lines',
            'default_res_id': self.id,
            'default_use_template': bool(mail_template_id),
            'default_template_id': mail_template_id.id,
            'default_composition_mode': 'comment',
            'default_attachment_ids': attachments,
            'local_transfer_date': local_transfer_date if local_transfer_date else None
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'target': 'new',
            'context': ctx,
        }

class SendMailExtended(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _action_send_mail(self, auto_commit=False):
        """
        Sends mail and updates the `is_mail_sent` flag for delivery merchant payout.
        If an error occurs during mail sending, a `ValidationError` is raised.
        """
        active_model = self.env.context.get('active_model')
        if not active_model or active_model != 'delivery.merchant.payout.lines':
            return super(SendMailExtended, self)._action_send_mail(auto_commit=auto_commit)
        obj = self.env[active_model].browse(self.env.context.get('active_id'))
        try:
            result = super(SendMailExtended, self)._action_send_mail(auto_commit=auto_commit)
            obj.is_mail_sent = True
        except Exception:
            raise ValidationError(_('Failed to send the email. Please try again later.'))
        return result