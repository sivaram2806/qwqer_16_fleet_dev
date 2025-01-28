# -*- coding: utf-8 -*-

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Modified res.partner to add fields'

    emp_id = fields.Many2one('hr.employee', "Employee")
    driver_uid = fields.Char(string='Driver ID', index=True)
    property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
        string="Account Payable",
        domain="[('deprecated', '=', False), ('company_id', '=', current_company_id)]",
        help="This account will be used instead of the default one as the payable account for the current partner",
        required=True)
    property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
        string="Account Receivable",
        domain="[('deprecated', '=', False), ('company_id', '=', current_company_id)]",
        help="This account will be used instead of the default one as the receivable account for the current partner",
        required=True)