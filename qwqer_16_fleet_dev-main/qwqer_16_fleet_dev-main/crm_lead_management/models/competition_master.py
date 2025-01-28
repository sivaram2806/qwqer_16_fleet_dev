from odoo import api, fields, models, _


class CompetitionMaster(models.Model):
    _name = "competition.master"
    _description = "Competition Mater"

    name = fields.Char("Name")
