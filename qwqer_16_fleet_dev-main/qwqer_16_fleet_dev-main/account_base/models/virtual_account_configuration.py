# -*- coding: utf-8 -*-
from odoo import models, fields


class VirtualAccountConfiguration(models.Model):
    _name = 'virtual.account.configuration'
    _description = 'Virtual Account Configuration'
    _rec_name = "partner_type"

    journal_id = fields.Many2one("account.journal", string='Journal')
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], )
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method', )
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money'),
                                     ('transfer', 'Internal Transfer')], string='Payment Type')
    is_validated = fields.Boolean(string="Validate")
    # Company id for Multi-Company
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
