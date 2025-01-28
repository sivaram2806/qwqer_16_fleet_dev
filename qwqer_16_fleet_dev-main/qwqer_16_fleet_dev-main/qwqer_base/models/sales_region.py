# -*- coding: utf-8 -*-

from odoo import models, fields


class SalesRegion(models.Model):
    """
    This model contains record of sales regions, #V13_model name: region
    """
    _name = 'sales.region'
    _description = 'Sales region'
    _rec_name = 'name'

    name = fields.Char(string="Region Name", required=True)
    region_code = fields.Char(string="Code", required=True, copy=False,
                              help="Add a unique CODE for this region")
    country_id = fields.Many2one(comodel_name="res.country", string="Country",
                                 default=lambda self: self.env.company.country_id,
                                 help="Select the respective country where this region belongs.")
    state_id = fields.Many2one(comodel_name='res.country.state', string="State",
                               domain="[('country_id', '=', country_id)]",
                               help="Select the respective state where this region belongs.")
    sale_zone_id = fields.Many2one(comodel_name="sales.zone",
                                   string="Sale Zone", ondelete='cascade',
                                   help="Select the respective sales zone where this region belongs.")
    analytic_account_id = fields.Many2one(comodel_name="account.analytic.account",
                                          string="Analytic Account",
                                          help="Please select an analytic account if this region have any "
                                               "specific analytic account")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    _sql_constraints = [('region_code_unique', 'unique(region_code,company_id)', 'Region code is already taken')]
