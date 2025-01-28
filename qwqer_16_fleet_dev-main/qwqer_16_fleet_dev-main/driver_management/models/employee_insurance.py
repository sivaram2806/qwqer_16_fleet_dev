# -*- coding:utf-8 -*-

from odoo import fields, models

class EmployeeInsurance(models.Model):
    """
    Model contains records from Hr Employee Insurance Details
    """
    _name = 'employee.insurance.policy'
    _description = 'Employee Insurance Policy'

    name = fields.Text("Name")
    dob = fields.Date(string='DOB')
    policy_num = fields.Char(string="Policy Number")
    nominee_type = fields.Many2one('nominee.type', string="Nominee Relation")
    emp_id = fields.Many2one('hr.employee', string='Employee')