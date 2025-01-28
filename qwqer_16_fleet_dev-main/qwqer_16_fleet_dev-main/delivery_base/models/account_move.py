# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    merchant_payout_id = fields.Many2one('delivery.merchant.payout', string='Merchant Payout',copy=False)
    merchant_order_id = fields.Many2one(comodel_name='sale.order', string='Merchant Sale Order')
    order_id = fields.Char(string='Order ID',related='merchant_order_id.order_id',readonly=True)
    date_order = fields.Datetime(string='Order Date',related='merchant_order_id.date_order')



























