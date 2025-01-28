# -*- coding:utf-8 -*-

from odoo import fields, models

class EmployeeAssets(models.Model):
    """
    Model contains records from employee.assets
    """
    _name = 'employee.assets'
    _description = 'Employee Assets'

    asset_type_id = fields.Many2one('employee.asset.type', string="Asset Type")
    asset_details = fields.Char(string="Details")
    description = fields.Char(string="Description")
    emp_id = fields.Many2one('hr.employee', string='Employee')
