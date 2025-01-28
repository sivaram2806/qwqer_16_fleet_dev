# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CompanyExtended(models.Model):
    _inherit = 'res.company'

    cashfree_env = fields.Selection([('PROD', 'Production'), ('TEST', 'Test')], string='Cash Free Environment', )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cashfree_env = fields.Selection(related='company_id.cashfree_env', string='Cash Free Environment',readonly=False)
