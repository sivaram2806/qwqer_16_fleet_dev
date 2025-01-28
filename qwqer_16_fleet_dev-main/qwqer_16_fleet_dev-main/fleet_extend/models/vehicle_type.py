from odoo import fields, models, api


class VehicleType(models.Model):
    _name = 'vehicle.vehicle.type'
    _description = 'Vehicle Type'

    name = fields.Char(required=1)
    max_tonnage = fields.Float()
    height = fields.Float()
    width = fields.Float()
    length = fields.Float()

