# -*- coding: utf-8 -*-

from odoo import models, fields


class CustomerSegmentExtended(models.Model):

    _inherit = 'partner.segment'

    is_ftl = fields.Boolean(string="Is Ftl")
