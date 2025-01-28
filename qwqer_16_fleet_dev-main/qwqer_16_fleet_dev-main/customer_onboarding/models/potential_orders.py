# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PotentialOrders(models.Model):
    """ model for capturing potential order"""
    _name = "potential.orders"
    _description = "Potential Orders"

    name = fields.Char("Name")
    active = fields.Boolean(string="Active", default=True)
