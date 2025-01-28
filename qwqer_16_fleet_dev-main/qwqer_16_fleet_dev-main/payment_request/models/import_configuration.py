# -*- coding: utf-8 -*-

from odoo import api, fields, models


class BillImportConfig(models.Model):
    _name = 'bill.import.config'
    _description = 'Bill Import Configuration'

    name = fields.Char(string='Name')
    journal_id = fields.Many2one('account.journal', string='Journal')
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], )
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method', )
    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')],
        string='Payment Type', )
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
