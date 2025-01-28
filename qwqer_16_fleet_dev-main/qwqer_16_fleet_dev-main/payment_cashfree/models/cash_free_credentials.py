# -*- coding: utf-8 -*-
from odoo import models, fields


class CashFreeCredentials(models.Model):
    _name = 'cash.free.credentials'
    _description = 'Cash Free Credentials'

    name = fields.Char(string='APP ID')
    key = fields.Char(string='Secret Key')
    api_date = fields.Date(string="Last Settlement Date")
    public_key = fields.Binary(required=True, attachment=False, groups="base.group_system",
                               help="The key to call all cashfree API")
    public_key_filename = fields.Char()
    payout_status_date = fields.Date(string="Payout Status Update Date")
    payout_app_id = fields.Char(string="Payout Client ID")
    payout_key = fields.Char(string="Payout Secret Key")

    # Company id for Multi-Company property
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
