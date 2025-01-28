# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CompanyExtended(models.Model):
    _inherit = 'res.company'

    qwqer_shop_product_id = fields.Many2one('product.template')
    qwqer_shop_credit_journal_id = fields.Many2one('account.journal', string='Journal')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    qwqer_shop_product_id = fields.Many2one(related='company_id.qwqer_shop_product_id', readonly=False)
    qwqer_shop_credit_journal_id = fields.Many2one(related='company_id.qwqer_shop_credit_journal_id', readonly=False,
                                                   string='Journal')
