# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrEmployeeShiftType(models.Model):
    """
    Model contains records from Employee Shift Type, #V13_model name: employee.shift.type
    """
    _name = 'hr.employee.shift.type'
    _description = 'Employee Shift Type'
    _rec_name = 'name'
    _order = 'name asc'


    name = fields.Char("Name")
    code = fields.Char("Code")