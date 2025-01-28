# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CustomerAdditionalCharges(models.Model):
    _inherit = "customer.additional.charges"
    _description = "Customer additional Charges"

    customer_onboard_id = fields.Many2one(comodel_name='customer.onboard', string='Customer Onboard Id')

    @api.model
    def create(self, values):
        res = super(CustomerAdditionalCharges, self).create(values)
        if values.get('customer_onboard_id'):
            result = self.search([('customer_onboard_id', '=', res.customer_onboard_id.id), ('charge_type_id', '=', res.charge_type_id.id)])
            if result and len(result) > 1:
                raise UserError(
                    _("In the additional charges section, the same charge type %s are added multiple times.Please remove the duplicates.") % (
                        res.charge_type_id.name))
        return res

    def write(self, values):
        res = super(CustomerAdditionalCharges, self).write(values)
        if values.get('charge_type_id'):
            result = self.search([('customer_onboard_id', '=', self.customer_onboard_id.id), ('charge_type_id', '=', self.charge_type_id.id)])
            if result and len(result) > 1:
                raise UserError(
                    _("In the additional charges section, the same charge type %s are added multiple times.Please remove the duplicates.") % (
                        self.charge_type_id.name))
        return res
