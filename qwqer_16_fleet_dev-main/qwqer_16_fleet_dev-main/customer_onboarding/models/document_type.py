# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class DocumentType(models.Model):
    _inherit = "partner.document.line"
    _description = "Document Type"


    customer_onboard_id = fields.Many2one(comodel_name='customer.onboard',
                                          string='Document')
    pricing_plan_customer_ob_id = fields.Many2one(comodel_name='customer.onboard',
                                                  string='Document')
    kyc_customer_ob_id = fields.Many2one(comodel_name='customer.onboard',
                                         string='Document')
    quotation_customer_ob_id = fields.Many2one(comodel_name='customer.onboard',
                                               string='Document')

    agreement_customer_ob_id = fields.Many2one(comodel_name='customer.onboard',
                                               string='Document')
