# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CustomerWalletConfig(models.Model):
    _name = 'customer.wallet.config'
    _description = 'configuration model for storing the wallet configuration'
    _rec_name = "journal_id"

    journal_id = fields.Many2one(comodel_name="account.journal", string='Wallet Journal')
    default_credit_account_id = fields.Many2one(comodel_name="account.account", string='Default Credit Account')
    default_debit_account_id = fields.Many2one(comodel_name="account.account", string='Default debit Account')
    wallet_debit_account_id = fields.Many2one(comodel_name="account.account", string='Wallet Debit Account')
    wallet_inter_account_id = fields.Many2one(comodel_name="account.account", string='Intermediate Wallet Account')
    merchant_inter_account_id = fields.Many2one(comodel_name="account.account", string='Intermediate Merchant Wallet Account')
    wallet_round_off_account_id = fields.Many2one(comodel_name="account.account", string='Wallet Round-off Account')
    wallet_payment_method_id = fields.Many2one(comodel_name='account.payment.method', string='Wallet Payment Method')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
