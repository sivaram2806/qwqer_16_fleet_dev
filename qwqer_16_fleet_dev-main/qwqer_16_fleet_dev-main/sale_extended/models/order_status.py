from odoo import fields, models


class OrderStatus(models.Model):
    _name = 'order.status'
    _description = 'Order Status'

    name = fields.Char(string='Status')
    code = fields.Char(string='Code')
    is_cancel_order = fields.Boolean(string='Cancel Sale Order')
