# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PartnerSegment(models.Model):
    _name = 'partner.segment'
    _description = 'Partner Segment'

    name = fields.Char()
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    is_customer = fields.Boolean(string='Is a Customer?')
    is_vendor = fields.Boolean(string='Is a Vendor?')

    _sql_constraints = [
        ('name_company_uniq', 'unique (name,company_id)',
         'The  Name must be unique per Company !')
    ]
