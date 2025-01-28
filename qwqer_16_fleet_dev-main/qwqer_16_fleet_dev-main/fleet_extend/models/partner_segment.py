# -*- coding: utf-8 -*-

from odoo import fields, models


class PartnerSegment(models.Model):
    _inherit = 'partner.segment'

    is_fleet_service = fields.Boolean(string='Is Fleet Service', default=False)
    is_ftl = fields.Boolean(string="Is Ftl")

