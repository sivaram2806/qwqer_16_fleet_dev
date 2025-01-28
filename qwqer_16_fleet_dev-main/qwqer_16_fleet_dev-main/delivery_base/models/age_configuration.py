from odoo import models, fields, api


class AgeConfiguration(models.Model):
    _name = 'qwqer.age.configurations'
    _description = 'Age Configuration'

    name = fields.Char(string='Name', required=True)
    no_of_days = fields.Integer('No of Days', copy=False, default=0)