# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_req_id = fields.Many2one('payment.request', string='Request ID', copy=False)
    bank_transfer_id = fields.Char(string='Bank Transfer ID', copy=False)

    def unlink(self):
        for rec in self:
            if rec.payment_req_id:
                rec.payment_req_id.state = 'payment_request'
        return super(AccountMove, self).unlink()

    def button_draft(self):
        result = super(AccountMove, self).button_draft()
        for rec in self:
            if rec.payment_req_id:
                rec.payment_req_id.state = 'vendorbill_prepared'
        return result

    def action_post(self):
        result = super(AccountMove, self).action_post()
        for rec in self:
            if rec.payment_req_id:
                rec.payment_req_id.state = 'vendorbill_posted'
        return result

    def button_cancel(self):
        result = super(AccountMove, self).button_cancel()
        for rec in self:
            if rec.payment_req_id:
                rec.payment_req_id.state = 'cancelled'
        return result


    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',)
    def _compute_amount(self):
        res  = super(AccountMove, self)._compute_amount()
        for rec in self:
            if rec.payment_req_id:
                if rec.payment_state =="paid" and rec.state == "posted" :
                    rec.payment_req_id.state="payment_processed"
                elif rec.payment_state !="paid" and rec.state == "posted" :
                    rec.payment_req_id.state="vendorbill_posted"
        return res

