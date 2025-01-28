# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResPartner(models.Model):
    """ The model res_partner is inherited to make modifications """
    _inherit = 'res.partner'

    # invoice_frequency_id = fields.Many2one('invoice.frequency', 'Invoice Frequency')
    brand_name = fields.Char()
    pick_up_area = fields.Text(string="Pick up Area")
    item_category_id = fields.Many2one(comodel_name="item.category", string="Item Category")
    source_lead_type_id = fields.Many2one(comodel_name='utm.source', string="Source/Lead Type")
    industry_id = fields.Many2one(comodel_name='res.partner.industry', string='Customer Industry')
    followup_status_id = fields.Many2one(comodel_name="mail.activity.type", string="Follow-up Status")
    pricing_type = fields.Selection([('default', 'Default Pricing'),
                                     ('special', 'Special Pricing')], )
    delivery_type_id = fields.Many2one(comodel_name='delivery.type', string='Type of Delivery')
    payment_mode_ids = fields.Many2many(comodel_name='payment.mode', string='Payment Mode')
    merchant_amount_collection = fields.Selection(selection=[('yes', 'Yes'),
                                                             ('no', 'No')],
                                                  string="Merchant Amount Collection", default='no')
    # is_credit_bool = fields.Boolean(string="Is Credit", compute='_compute_is_credit_bool', store=True)
    amount_collection_limit = fields.Float(string="Amount Collection Limit")
    amount_collection_sign = fields.Char(string="Amount Collection Sign", default="Rs")
    settlement_time_id = fields.Many2one(comodel_name='settlement.time', string='Settlement Time')
    collection_charges = fields.Float(string="Collection Charges")
    collection_charges_sign = fields.Char(string="Collection Charges Sign", default="%")
    distance_limitation = fields.Float(string="Distance Limitation", copy=False)
    potential_orders_id = fields.Many2one(comodel_name='potential.orders', string="Potential Orders", copy=False)
    api_selection = fields.Selection(selection=[('yes', 'Yes'),
                                                ('no', 'No')],
                                     string="API", default='no', copy=False)
    product_storage = fields.Selection(selection=[('yes', 'Yes'),
                                                  ('no', 'No')],
                                       string="Product Storage", default='no', copy=False)
    product_sorting = fields.Selection(selection=[('yes', 'Yes'),
                                                  ('no', 'No')],
                                       string="Product Sorting", default='no', copy=False)
    sms_alert = fields.Selection(selection=[('yes', 'Yes'),
                                            ('no', 'No')],
                                 string="Customer SMS Alert")
    email_alert = fields.Selection(selection=[('yes', 'Yes'),
                                              ('no', 'No')],
                                   string="Customer Email Alert")
    is_fifo_flow = fields.Selection(selection=[('yes', 'Yes'),
                                               ('no', 'No')
                                               ], string='FIFO Flow', default='no')
    max_no_de = fields.Integer(string='Max No of DE', default=False)
    product_line_id = fields.Many2one(comodel_name="product.lines", string="Product Lines")
    source_type_id = fields.Many2one(comodel_name="source.type", string="Order Placement")
    customer_status = fields.Selection(selection=[('new_customer', 'New Merchant'),
                                                  ('existing_customer', 'New Sub Merchant')],
                                       string="Customer Status", default='new_customer')
    is_a_sub_customer = fields.Boolean(string="Is a Sub Customer")
    parent_partner_id = fields.Many2one(comodel_name='res.partner', string="Parent Merchant")
    merchant_phone_number = fields.Char("Merchant Phone Number")
    submerchant_billing = fields.Selection(selection=[('sub_merchant', 'Sub-Merchant'),
                                                      ('main_merchant', 'Main-Merchant')],
                                           string="Sub-Merchant Billing", default='sub_merchant')
    vehicle_invoice_frequency = fields.Selection(selection=[("weekly", "Weekly"), ("monthly", "Monthly"),
                                            ], default="weekly", copy=False, string="Vehicle Invoice Frequency")
    invoice_frequency_id = fields.Many2one(comodel_name='invoice.frequency', string='Customer Invoice Frequency')
    credit_period_id = fields.Many2one(comodel_name='account.payment.term', string='Credit Period')


    # @api.depends('payment_mode_ids')
    # def _compute_is_credit_bool(self):
    #     for rec in self:
    #         rec.is_credit_bool = False
    #         for payment in rec.payment_mode_ids:
    #             if payment.is_credit_payment:
    #                 rec.is_credit_bool = True