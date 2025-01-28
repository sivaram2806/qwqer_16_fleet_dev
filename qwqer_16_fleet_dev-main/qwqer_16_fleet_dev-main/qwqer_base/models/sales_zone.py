# -*- coding: utf-8 -*-

from odoo import models, fields


class SalesZone(models.Model):
    """
    This model contains records on sales sales zone, #V13_model name: substate
    """
    _name = 'sales.zone'
    _description = 'Sales zone'
    _rec_name = 'name'

    name = fields.Char(string="Zone Name", required=True)
    country_id = fields.Many2one(comodel_name="res.country", string="Country",
                                 default=lambda self: self.env.company.country_id,
                                 help="Select the respective country where this zone belongs.")
    state_id = fields.Many2one(comodel_name='res.country.state', string="State",
                               domain="[('country_id', '=', country_id)]",
                               help="Select the respective state where this zone belongs.")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

