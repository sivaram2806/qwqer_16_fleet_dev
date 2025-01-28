# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CompanyExtended(models.Model):
    _inherit = 'res.company'
    back_days = fields.Integer(string='Back Days')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    back_days = fields.Integer(related='company_id.back_days', string='Back Days', readonly=False)
