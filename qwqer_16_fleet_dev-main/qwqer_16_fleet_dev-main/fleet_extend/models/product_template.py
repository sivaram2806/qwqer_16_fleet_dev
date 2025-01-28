from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fleet_ok = fields.Boolean(string='Can be Fleet')