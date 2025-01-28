from odoo import api, fields, models, _


class ProductLines(models.Model):
    _name = "product.lines"
    _description = "Product Lines"

    name = fields.Char("Name")
    active = fields.Boolean("Active", default=True)