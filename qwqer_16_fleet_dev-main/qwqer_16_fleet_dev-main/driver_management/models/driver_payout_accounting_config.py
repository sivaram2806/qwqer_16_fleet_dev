from odoo import api, fields, models


class PayoutConfig(models.Model):
    _name = 'driver.payout.accounting.config'
    _description = 'Driver Payout Accounting Configuration'
    _rec_name = 'expense_journal_id'

    expense_journal_id = fields.Many2one('account.journal', string='Expense Journal')
    expense_debit_account_id = fields.Many2one('account.account', string='Expense Debit Account')
    expense_credit_account_id = fields.Many2one('account.account', string='Expense Credit Account')
    expense_deduction_account_id = fields.Many2one('account.account', string='Expense Deduction Account')
    transfer_debit_account_id = fields.Many2one('account.account', string='Transfer Debit Account')
    transfer_credit_account_id = fields.Many2one('account.account', string='Transfer Credit Account')
    transfer_journal_id = fields.Many2one('account.journal', string='Transfer Journal')
    tds_account_id = fields.Many2one('account.account', string='TDS Account')
    tds_tax_id = fields.Many2one('account.tax', string='TDS Tax')
    vendor_payout_account_id = fields.Many2one('account.account', string='Deduction Account')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.company)