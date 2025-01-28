# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountPaymentExtend(models.Model):
    _inherit = "account.payment"
    claim_id = fields.Many2one(comodel_name='hr.expense.claim', string="Expense Claim", ondelete='cascade', copy=True)


class AccountPaymentRegisterExtended(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        res = super()._create_payments()
        claim_id = self.env.context.get('claim_id')
        if claim_id:
            claim = self.env['hr.expense.claim'].browse(claim_id)
            if claim:
                claim.payment_ids = [(4, res.id)]
                res.claim_id = claim_id
        return res
