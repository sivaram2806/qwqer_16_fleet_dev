# -*- coding:utf-8 -*-

from odoo import fields, models

class EmployeeAssetType(models.Model):
    _name = 'employee.asset.type'
    _description = 'Document Type'

    name = fields.Char('Type')
