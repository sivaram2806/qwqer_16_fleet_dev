# -*- coding: utf-8 -*-
from odoo import fields, models


class MerchantPayoutQshopConfig(models.Model):
    _inherit = 'merchant.payout.account.config'

    qshop_credit_transfer_account_id = fields.Many2one('account.account', string='Qwqer Shop Transfer Credit Account')
    qshop_debit_transfer_account_id = fields.Many2one('account.account', string='Qwqer Shop Transfer Deduction Account')
    qshop_transfer_journal_id = fields.Many2one('account.journal', string='Qwqer Shop Transfer Journal')
    qshop_tds_tax_id = fields.Many2one('account.tax', string='Shop TDS Tax')
    qshop_tds_tax_payble = fields.Many2one('account.account', string='TDS Tax Payable Account')