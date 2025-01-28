# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CustomerAdditionalCharges(models.Model):
    _inherit = "customer.additional.charges"
    _description = "Customer Additional Charges"

    change_request_id = fields.Many2one(comodel_name='customer.master.change.request', string='Change Request')
    previous_change_request_id = fields.Many2one(comodel_name='customer.master.change.request', string='Previous Change Request')
    additional_charge_id = fields.Many2one(comodel_name='customer.additional.charges')
    is_changed = fields.Boolean(string="Is Changed")
