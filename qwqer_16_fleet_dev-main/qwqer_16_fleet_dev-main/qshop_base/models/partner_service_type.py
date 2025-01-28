# -*- coding: utf-8 -*-

from odoo import fields, models


class PartnerServiceTypeExtend(models.Model):
    _inherit = 'partner.service.type'

    is_qshop_service = fields.Boolean(string='Is Qshop Service', default=False)

