# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class CustomerWalletDetailedReport(models.Model):
    _name = "customer.wallet.detailed.report"
    _description = "Customer Wallet Detailed Report"
    _auto = False
    _rec_name = 'partner_id'
    _order = 'id desc'

    partner_id = fields.Many2one(comodel_name='res.partner',string= 'Partner', index=True)
    debit_amt = fields.Float('Debit')
    credit_amt = fields.Float("Credit")
    balance_amt = fields.Float("Balance")
    create_dt = fields.Datetime(string="Date")
    reference = fields.Char("Status")
    wallet_balance = fields.Float("Wallet Balance")
    label = fields.Char("Transactions")
    move_name = fields.Char('ERP Reference No.')
    wallet_transaction_ref_id = fields.Char(string='Wallet Transaction No.')
    wallet_order_id = fields.Char(string='Wallet Order ID')
    comments = fields.Text("Remarks")
    phone_number = fields.Char(string="Phone No.")
    order_transaction_no = fields.Char(string='Wallet Order Transaction No', index=True)


        

