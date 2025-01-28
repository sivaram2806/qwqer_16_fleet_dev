# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CompanyExtended(models.Model):
    _inherit = 'res.company'
    fleet_invoice_product_id = fields.Many2one(comodel_name='product.product', string='Product')
    fleet_bill_account_id = fields.Many2one(comodel_name='account.account', string='Account')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fleet_invoice_product_id = fields.Many2one(related='company_id.fleet_invoice_product_id',
                                               comodel_name='product.product', string='Product', readonly=False)
    fleet_bill_account_id = fields.Many2one(related='company_id.fleet_bill_account_id', comodel_name='account.account',
                                            string='Account', readonly=False)
