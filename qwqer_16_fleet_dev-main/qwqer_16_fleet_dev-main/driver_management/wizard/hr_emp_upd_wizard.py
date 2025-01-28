# -*- coding: utf-8 -*-
from odoo import fields, models

class HrEmployeeUpdateWizard(models.TransientModel):
    _inherit = "hr.employee.update.wizard"
    _description = "Custom model to update hr employee data in bulk"


    employee_type = fields.Selection(selection_add=[('driver', 'Driver'),
                                                    ('sales_person', 'Sales Person')], string='Employee Type')
    action_type = fields.Selection(selection_add=[('related_partner', 'Update Related Partner'),
                                                  ('related_partner_driver_id', 'Update Related Partner Driver ID')])
