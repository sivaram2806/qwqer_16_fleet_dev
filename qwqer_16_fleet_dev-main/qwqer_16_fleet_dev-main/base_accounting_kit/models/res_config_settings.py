# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    customer_credit_limit = fields.Boolean(string="Customer Credit Limit", readonly=False,
                                           related='company_id.customer_credit_limit')

    use_anglo_saxon_accounting = fields.Boolean(string="Use Anglo-Saxon accounting", readonly=False,
                                                related='company_id.anglo_saxon_accounting')
    credit_limit_warning_percent = fields.Float(string="Credit Limit Warning Percentage", readonly=False,
                                                     related='company_id.credit_limit_warning_percent')
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        customer_credit_limit = params.get_param('customer_credit_limit',
                                                 default=False)
        res.update(customer_credit_limit=customer_credit_limit)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            "customer_credit_limit",
            self.customer_credit_limit)

    @api.constrains('credit_limit_warning_percent')
    def _check_setting_field(self):
        for record in self:
            if record.credit_limit_warning_percent > 100:
                raise ValidationError("Percentage Must be below or equal to 100")