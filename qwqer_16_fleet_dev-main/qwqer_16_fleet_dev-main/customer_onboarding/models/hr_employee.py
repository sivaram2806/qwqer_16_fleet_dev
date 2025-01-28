# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee'
    
    mu_id = fields.Many2one(comodel_name='hr.employee', string='MU')

class HrEmployeePublicExtended(models.Model):
    """Modification in hr.employee.public will be added in this inherited class"""
    _inherit = "hr.employee.public"

    mu_id = fields.Many2one(comodel_name='hr.employee', string='MU')