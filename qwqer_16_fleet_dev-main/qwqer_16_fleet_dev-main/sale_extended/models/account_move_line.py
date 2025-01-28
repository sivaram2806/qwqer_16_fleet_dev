# -*- coding: utf-8 -*-


from odoo import models, fields

class AccountMoveLine(models.Model):
    """
     inherited for adding fields for qwqer service
     """
    _inherit = 'account.move.line'

    merchant_order_id = fields.Many2one(comodel_name='sale.order', string='Merchant Sale Order')
    is_so_inv_line = fields.Boolean(string='Is SO Invoice Line', default=False)
    order_id = fields.Char(string='Order ID', related='merchant_order_id.order_id', readonly=True)
    date_order = fields.Datetime(string='Order Date', related='merchant_order_id.date_order')
