# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date

from dateutil.relativedelta import relativedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    b2b_invoice_tax_ids = fields.Many2many('account.tax', 'b2b_invoice_tax', 'partner1_id', 'tax1_id',
                                           string='B2B Invoice Tax',domain="[('price_include','=', False)]")
    b2b_sale_order_tax_ids = fields.Many2many('account.tax', 'b2b_sale_order_tax', 'partner2_id', 'tax2_id',
                                              string='B2B Sale Order Tax',domain="[('price_include','=', True)]")

    is_delivery_customer = fields.Boolean(string='Is Delivery Customer')

    pricing_model = fields.Selection(selection=[('KM', 'KM'),
                                                ('slab', 'SLAB'),
                                                ('flat', 'FLAT')],
                                     string="Pricing Model", default='KM', copy=False)

    km_pricing_plan_ids = fields.One2many(comodel_name='pricing.plan', inverse_name='partner_id',
                                          string='Km Pricing Plan',domain=[('select_plan_type', '=', 'KM')])
    slab_pricing_plan_ids = fields.One2many(comodel_name='pricing.plan', inverse_name='partner_id',
                                            string='Slab Pricing Plan',domain=[('select_plan_type', '=', 'slab')])
    flat_pricing_plan_ids = fields.One2many(comodel_name='pricing.plan', inverse_name='partner_id',
                                            string='Flat Pricing Plan',domain=[('select_plan_type', '=', 'flat')])

    additional_charges_ids = fields.One2many(comodel_name='customer.additional.charges', inverse_name='partner_id')


    @api.onchange('service_type_id')
    def get_service_type_delivery(self):
        if self.service_type_id and self.service_type_id.is_delivery_service:
            self.is_delivery_customer = True
        else:
            self.is_delivery_customer = False






