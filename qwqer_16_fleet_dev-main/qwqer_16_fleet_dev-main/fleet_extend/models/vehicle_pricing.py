# -*- coding: utf-8 -*-

from odoo import fields, models


class FleetVehiclePricing(models.Model):
    """
    This model contains record of vehicle pricing, V13 model name: price.config
    """
    _name = 'vehicle.pricing'
    _description = 'Vehicle Pricing'
    _rec_name = 'name'
    _order = 'name asc'

    name = fields.Char(string="Name", required=True)
    vehicle_model_id = fields.Many2one(comodel_name="fleet.vehicle.model", string="Vehicle Model", required=True)
    partner_id = fields.Many2one('res.partner',
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    # Company id for Multi-Company property
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)


