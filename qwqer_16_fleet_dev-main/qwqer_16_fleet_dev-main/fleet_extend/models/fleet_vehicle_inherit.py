# -*- coding: utf-8 -*-

from odoo import fields, models


class FleetVehicleModel(models.Model):
    """
    The model fleet.vehicle.model is inherited to make modifications, #V13_model name:fleet.vehicle.model
    """
    _inherit = 'fleet.vehicle.model'
    _description = 'Model of a vehicle'

    manager_id = fields.Many2one(comodel_name='res.users', string="Fleet Manager")
