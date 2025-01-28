# -*- coding:utf-8 -*-

from odoo import fields, models


class AccountAccountCustom(models.Model):
    _inherit = 'account.account'

    is_driver_account = fields.Boolean(string='Is Driver Account')
    is_expense_credit = fields.Boolean(string='Is Expense Credit Account')
    default_employee_account = fields.Boolean(string='Is Default Employee Account')