# -*- coding:utf-8 -*-

from odoo import api, fields, models


class DriverVehicleCategory(models.Model):
    """
    Model contains records from vehicle category, #V13_model name: vehicle.category
    """
    _name = 'driver.vehicle.category'
    _description = 'Vehicle Category'

    name = fields.Char('Name',tracking=True)
    code = fields.Char('Code', tracking=True)