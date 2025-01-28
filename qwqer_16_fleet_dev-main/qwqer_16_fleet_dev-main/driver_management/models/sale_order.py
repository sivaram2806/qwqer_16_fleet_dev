# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

class SaleOrderDriverManagement(models.Model):
    """This model Sale.Order is inherited to make modification for driver"""
    _inherit = 'sale.order'

    vehicle_type = fields.Char(string='Vehicle Type')
    vehicle_category_id = fields.Many2one(comodel_name='driver.vehicle.category', string='Vehicle Category')
    order_cost = fields.Float(string='Avg Cost Per Order',digits='Product Price',group_operator="sum")


    @api.onchange('driver_id')
    def onchange_driver_id(self):
        res = super(SaleOrderDriverManagement,self).onchange_driver_id()
        if self.driver_id:
            self.vehicle_type = self.driver_id.vehicle_type
            self.vehicle_category_id = self.driver_id.vehicle_category_id.id
        return res