# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ItemCategory(models.Model):
    """model for store the item category"""
    _name = "item.category"
    _description = "Item Category Configuration"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
