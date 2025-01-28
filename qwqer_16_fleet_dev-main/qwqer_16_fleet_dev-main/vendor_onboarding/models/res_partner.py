# -*- coding: utf-8 -*-

from odoo import api, fields, models
from lxml import etree


class ResPartner(models.Model):
    """ The model res_partner is inherited to make TDS related modifications """
    _inherit = 'res.partner'

    tax_tds_id = fields.Many2one('account.tax', string="TDS", domain=[('is_tds', '=', True), ('price_include', '=', False)])