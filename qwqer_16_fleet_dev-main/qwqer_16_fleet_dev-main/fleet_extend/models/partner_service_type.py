# -*- coding: utf-8 -*-

from odoo import fields, models


class PartnerServiceTypeExtend(models.Model):
    _inherit = 'partner.service.type'

    is_fleet_service = fields.Boolean(string='Is Fleet Service', default=False)

