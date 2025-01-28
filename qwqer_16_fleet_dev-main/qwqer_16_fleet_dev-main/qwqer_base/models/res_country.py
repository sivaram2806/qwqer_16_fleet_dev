# -*- coding: utf-8 -*-

from odoo import fields, models


class CountryState(models.Model):
    """ The model res.country.state is inherited to make modifications """
    _inherit = 'res.country.state'

    regions_ids = fields.One2many(comodel_name='sales.region', inverse_name='state_id', string='Sales Regions')
    zones_ids = fields.One2many(comodel_name='sales.zone', inverse_name='state_id', string='Sales Zones')

