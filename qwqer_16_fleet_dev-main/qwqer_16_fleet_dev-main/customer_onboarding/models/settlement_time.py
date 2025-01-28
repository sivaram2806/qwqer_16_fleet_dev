# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SettlementTime(models.Model):
    _name = "settlement.time"
    _description = "Settlement Time"
    
    
    name = fields.Char("Name")
    active = fields.Boolean("Active", default=True)