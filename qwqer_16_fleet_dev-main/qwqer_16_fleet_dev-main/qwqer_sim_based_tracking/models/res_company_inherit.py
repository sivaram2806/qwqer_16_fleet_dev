from odoo import fields, models, api


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    tracking_provider = fields.Selection([("traqo", "Traqo"), ("traqo_test", "Traqo Test")], readonly=False,store=True)
    track_username = fields.Char(string="Username", readonly=False, store=True)
    track_password = fields.Char(string="Password", readonly=False, store=True)