# -*- coding: utf-8 -*-

from odoo import models, fields


class CashFreeConfiguration(models.Model):
    _name = 'cash.free.configuration'
    _description = 'Cash Free Configuration'
    _rec_name = "name"

    name = fields.Char(string="Configuration Name")
    partner_id = fields.Many2one('res.partner', string='Partner',
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    journal_id = fields.Many2one("account.journal", string='Journal', required=True)
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], required=True)
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money'),
                                     ('transfer', 'Internal Transfer')], string='Payment Type', required=True)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method', required=True)
    is_validated = fields.Boolean(string="Validate Payment Automatically", required=True)

    # Company id for Multi-Company property
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
