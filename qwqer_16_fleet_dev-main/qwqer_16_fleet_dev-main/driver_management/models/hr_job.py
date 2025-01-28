# -*- coding:utf-8 -*-

from odoo import api, fields, models


class HrJob(models.Model):
    _inherit = "hr.job"

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        related_emp_account = self.env['account.account'].search([('deprecated', '=', False),
                                                                  ('default_employee_account', '=', True)], limit=1)
        res.update({'account_id': related_emp_account.id})
        return res

    account_id = fields.Many2one('account.account', string='Related Employee Account',
                                 domain="[('deprecated', '=', False), ('default_employee_account', '=', True)]")