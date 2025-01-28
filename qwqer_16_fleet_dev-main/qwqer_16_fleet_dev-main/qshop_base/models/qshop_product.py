from odoo import models, fields


class QwqerShopProduct(models.Model):
    _name = 'qshop.product.lines'
    _description = "Qwqer Shop Products"

    name = fields.Char(string='SKU')
    item_name = fields.Char(string='Item Name')
    weight = fields.Char(string='Weight')
    units = fields.Integer(string="Quantity")
    sell_price = fields.Float(string="Selling Price")
    mark_price = fields.Float(string="MRP")
    total_price = fields.Float(string="Total Price")
    sale_order_id = fields.Many2one('sale.order', string="Qwqer Shop Order")