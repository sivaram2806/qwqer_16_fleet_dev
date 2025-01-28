# -*- coding: utf-8 -*-
from odoo import fields, models


class MerchantPayoutConfig(models.Model):
    _name = 'merchant.payout.account.config'
    _description = 'Merchant Payout Accounting Configuration'

    register_payment_journal_id = fields.Many2one('account.journal', string='Register Payment Journal')
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], )
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method', )
    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')],
        string='Payment Type', )
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
