# -*- coding:utf-8 -*-

from odoo import fields, models

class NomineeType(models.Model):
    _name = 'nominee.type'
    _description = 'Employee Nominee Type'

    name = fields.Char('Nominee Relation')
