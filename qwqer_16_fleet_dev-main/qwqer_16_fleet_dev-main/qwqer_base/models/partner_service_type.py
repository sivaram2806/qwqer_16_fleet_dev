# -*- coding: utf-8 -*-

from odoo import fields, models


class PartnerServiceTypeConfig(models.Model):
    """model for storing the customer service type data"""
    _name = 'partner.service.type'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    is_customer = fields.Boolean(string='Is a Customer?')
    is_vendor = fields.Boolean(string='Is a Vendor?')


    _sql_constraints = [
        ('name_company_uniq', 'unique (name,company_id)',
         'The  Name must be unique per Company!'),
        ('code_company_uniq', 'unique (code,company_id)',
         'The Code must be unique per Company!!')
    ]
