from odoo import api, fields, models, _


class DeliveryType(models.Model):

    _name = "delivery.type"
    _description = "Delivery Type"

    name = fields.Char("Name")
    active = fields.Boolean("Active", default=True)