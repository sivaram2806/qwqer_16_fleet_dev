# -*- coding: utf-8 -*-
from odoo import fields, models


class CompanyExtended(models.Model):
    _inherit = 'res.company'

    journal_id = fields.Many2one(comodel_name="account.journal", string='Journal')
    is_validated = fields.Boolean(string="Validate")
    driver_credit_account = fields.Many2one(comodel_name='account.account', string='Driver Credit account')
    driver_debit_account = fields.Many2one(comodel_name='account.account', string='Driver debit account')
    driver_balance_token = fields.Char(string="Authorization Token")
    driver_balance_limit = fields.Integer(string="Limit")
    driver_balance_url = fields.Char(string="URL")


class ResConfigSettings(models.TransientModel):
    _inherit = ['res.config.settings']

    journal_id = fields.Many2one(related='company_id.journal_id', string='Journal', readonly=False, required=False)
    is_validated = fields.Boolean(related='company_id.is_validated', string="Validate", readonly=False, required=False)
    driver_credit_account = fields.Many2one(related='company_id.driver_credit_account', string='Driver Credit account',readonly=False, required=False)
    driver_debit_account = fields.Many2one(related='company_id.driver_debit_account', string='Driver debit account',readonly=False, required=False)
    driver_balance_token = fields.Char(related='company_id.driver_balance_token', string="Authorization Token", readonly=False)
    driver_balance_limit = fields.Integer(related='company_id.driver_balance_limit', string="Limit", readonly=False)
    driver_balance_url = fields.Char(related='company_id.driver_balance_url', string="URL", readonly=False)
