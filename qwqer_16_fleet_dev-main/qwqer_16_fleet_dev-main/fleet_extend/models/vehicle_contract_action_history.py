# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class VehicleContractActionHistory(models.Model):
    _name = "vehicle.contract.action.history"
    _description = "Vehicle Contract History"

    user_id = fields.Many2one('res.users')
    description = fields.Char(string="Comments")
    last_updated_on = fields.Datetime(string="Time of Action")
    vehicle_contract_id = fields.Many2one('vehicle.contract')
    action = fields.Char(string="Action Performed")
    
    
   
