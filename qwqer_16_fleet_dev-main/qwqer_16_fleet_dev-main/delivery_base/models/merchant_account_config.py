# -*- coding: utf-8 -*-
from odoo import fields, models


class MerchantPayoutDeliveryConfig(models.Model):
    _inherit = 'merchant.payout.account.config'

    delivery_credit_transfer_account_id = fields.Many2one('account.account', string='Qwqer Express Transfer Credit Account')
    delivery_debit_transfer_account_id = fields.Many2one('account.account', string='Qwqer Express Transfer Deduction Account')
    delivery_transfer_journal_id = fields.Many2one('account.journal', string='Qwqer Express Transfer Journal')