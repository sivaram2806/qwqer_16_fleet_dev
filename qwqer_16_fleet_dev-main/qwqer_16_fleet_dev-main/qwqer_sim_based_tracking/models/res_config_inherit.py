from odoo import fields, models, api


class ResconfigInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    tracking_provider = fields.Selection(
        related='company_id.tracking_provider', string="Service Provider", readonly=False)
    track_username = fields.Char(related='company_id.track_username', string="Username", readonly=False)
    track_password = fields.Char(related='company_id.track_password',string="Password", readonly=False)