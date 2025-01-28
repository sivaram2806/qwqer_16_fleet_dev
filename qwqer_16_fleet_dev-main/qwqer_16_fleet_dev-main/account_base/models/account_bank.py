# -*- coding: utf-8 -*-

from odoo import models, fields


class ResBank(models.Model):
    _inherit = 'res.bank'

    swift_code = fields.Char(string='SWIFT')
    is_virtual_account = fields.Boolean(string="Is Virtual Bank",default=False,copy=False)