from odoo import models, fields, api


class QwqerApiCredentials(models.Model):
    _name = 'qwqer.api.credentials'
    _description = 'QwqerApi'

    name = fields.Char(string='Database Name', required=True)
    server_url = fields.Char(string='Server URL', required=True)
    secret_key = fields.Char(string="Secret Key")
    authorization = fields.Char(string="Authorization")
    is_partner_sync = fields.Boolean(string="Enable Partner Sync")
    is_partner_create = fields.Boolean(string="Enable Create Partner ")
    is_partner_update = fields.Boolean(string="Enable Update Partner ")
    wallet_sync = fields.Boolean(string="Enable Wallet Sync ")
    wallet_journal = fields.Many2one('account.journal', string='Wallet Journal')
    wallet_sync_date_to = fields.Date("Wallet Balance Till Date")
    driver_balance_sync = fields.Boolean(string="Enable Driver Balance Sync ")
    driver_balance_journal = fields.Many2one('account.journal', string='Driver Balance Journal')
    driver_balance_date_to = fields.Date("Driver Balance Till Date")
    driver_account = fields.Many2one("account.account")
    wallet_account = fields.Many2one("account.account")
    offset_account = fields.Many2one("account.account")