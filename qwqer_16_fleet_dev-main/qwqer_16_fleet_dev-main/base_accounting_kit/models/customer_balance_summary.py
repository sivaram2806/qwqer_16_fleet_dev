# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api


class PartnerBalance(models.Model):
    _inherit = "partner.balance"
    _description = "Partner Balance"

    blocking_stage = fields.Float(string="Blocking Amount")

    @api.model
    def _select(self):
        rec = super()._select()
        rec+=''',
        rp.blocking_stage'''
        return rec