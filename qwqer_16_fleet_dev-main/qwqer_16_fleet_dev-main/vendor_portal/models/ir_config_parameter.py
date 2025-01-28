from odoo import _, api, fields, models, exceptions


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    @api.model
    def get_web_fleet_url(self):
        opts = [
            "web_fleet_url",
        ]
        return self.sudo().search_read([["key", "in", opts]], ["key", "value"])

