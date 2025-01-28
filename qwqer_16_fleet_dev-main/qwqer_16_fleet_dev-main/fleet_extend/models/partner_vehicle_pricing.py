# -*- coding: utf-8 -*-

from odoo import fields, models


class VehiclePricingLine(models.Model):
    """
    This model contains record of vehicle pricing lines, #V13_model name: vehicle.pricing
    """
    _name = 'partner.vehicle.pricing'
    _description = 'Partner Vehicle Pricing Line'

    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer",
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    base_dist = fields.Float(string='Base Distance') #V13_field: min_dist, model:vehicle.pricing
    base_cost = fields.Float(string='Base Cost', digits='Product Price') #V13_field: min_cost, model:vehicle.pricing
    charge_per_km = fields.Float(digits='Product Price') #V13_field: per_km_charge, model:vehicle.pricing
    trip_frequency = fields.Selection(selection=[("daily", "Daily"), ("monthly", "Monthly")],
                                      string="Calculation Method", default="daily", copy=False) #field: frequency, model:vehicle.pricing
    base_hrs = fields.Float(string="Base Hours")
    additional_cost = fields.Float(string="Additional Cost", digits='Product Price')
    additional_hrs = fields.Float(string="Additional Hours", digits='Product Price')
    vehicle_model_id = fields.Many2one(comodel_name='fleet.vehicle.model')
    # Company id for Multi-Company property
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
