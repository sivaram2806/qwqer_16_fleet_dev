# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class SourceType(models.Model):
    _name = "source.type"
    _description = "Source Types"

    name = fields.Char("Name")
    active = fields.Boolean("Active", default=True)
