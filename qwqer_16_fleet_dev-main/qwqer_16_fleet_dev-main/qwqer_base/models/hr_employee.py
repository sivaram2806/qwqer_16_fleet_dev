# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    """Modification in hr.employee will be added in this inherited module"""
    _inherit = 'hr.employee'

    region_id = fields.Many2one(comodel_name='sales.region', string="Region", domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    employee_status = fields.Selection([('active', 'Active'),
                                        ('inactive', 'Inactive')], string='Employee Status')
    driver_uid = fields.Char('Driver ID')


    def update_subordinates_to_user(self):
        for employee in self:
            try:
                if not employee.user_id and employee.child_ids:
                    continue

                emp_child_user_ids = employee.child_ids.filtered(lambda e: not e.driver_uid).mapped('user_id')
                if not emp_child_user_ids:
                    continue
                #TODO if subordinate_emp_user_ids is implemented
                # # Get the set of existing subordinates for quick lookup
                # existing_subordinates_ids = employee.user_id.subordinate_emp_user_ids
                # # Iterate only over child records whose user_id is not in existing subordinates
                # new_sub_ids = employee.child_ids.filtered(lambda e: e.user_id and e.user_id.id not in existing_subordinates_ids.ids)
                # new_sub_user_ids = list(new_sub_ids.mapped('user_id').ids)
                # for rec in new_sub_user_ids:
                #     employee.user_id.write({"subordinate_emp_user_ids": [(4, rec, 0)]})

                # Get the set of existing subordinates for quick lookup
                existing_subordinates_ids = self.env['res.users'].search([('manager_user_id', '=', employee.id)])

                # Iterate only over child records whose user_id is not in existing subordinates
                new_sub_ids = [item for item in emp_child_user_ids if item not in existing_subordinates_ids]
                for rec in new_sub_ids:
                    rec.manager_user_id = employee.user_id.id
            except Exception as e:
                raise ValidationError(_("Subordinates not updated\nError: %s") % str(e))

class HrEmployeePublicExtended(models.Model):
    """Modification in hr.employee.public will be added in this inherited class"""
    _inherit = "hr.employee.public"

    region_id = fields.Many2one(comodel_name='sales.region', string="Region", domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
