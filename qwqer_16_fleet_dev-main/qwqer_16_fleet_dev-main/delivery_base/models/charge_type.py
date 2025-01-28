from odoo import api, fields, models, _


class ChargeType(models.Model):
    _name = "charge.type"
    _description = "Charge Type"

    name = fields.Char("Name")
    active = fields.Boolean("Active", default=True)