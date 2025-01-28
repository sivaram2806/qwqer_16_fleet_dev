# -*- coding: utf-8 -*-

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Modified res.partner to add fields'

    contract_id = fields.Many2one(comodel_name='vehicle.contract', string='Contract Number')
    is_ftl_customer = fields.Boolean(string='Ftl Customer', related='segment_id.is_ftl')
    credit_period_id = fields.Many2one(comodel_name='account.payment.term', string='Credit Period')
    contact_designation = fields.Char(string='Contact Designation')
