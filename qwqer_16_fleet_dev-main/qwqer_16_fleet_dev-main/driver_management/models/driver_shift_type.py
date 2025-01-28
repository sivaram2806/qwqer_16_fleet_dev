# -*- coding:utf-8 -*-

from odoo import api, fields, models


class DriverShiftType(models.Model):
    _name = 'driver.shift.type'
    _description = 'Shift Type'

    name = fields.Char("Name")
    code = fields.Char("Code")