# -*- coding: utf-8 -*-

from odoo import models, fields

class MerchantOnlineJournalConfiguration(models.Model):
    """This model is for configuring the journal entry data for the qwqer shop merchant merchant.amount.configuration in odoo v13"""
    _inherit = 'merchant.journal.data.configuration'
    _description = 'Merchant Journal Data Configuration'

    qshop_journal_id = fields.Many2one("account.journal", string='QWQER Shop Journal')
    shop_merchant_discount_accid = fields.Many2one('account.account', string="Shop Merchant Discount Account")