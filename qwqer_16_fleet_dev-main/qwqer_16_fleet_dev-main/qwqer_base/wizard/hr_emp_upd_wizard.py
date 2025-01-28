# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployeeUpdateWizard(models.TransientModel):
    _name = "hr.employee.update.wizard"
    _description = "Custom model to update hr employee data in bulk"

    # Update region
    region_id = fields.Many2one(comodel_name='sales.region', string='Region')
    # update dept
    department_id = fields.Many2one('hr.department', 'Department')
    # update employee type
    employee_type = fields.Selection([
        ('employee', 'Employee'),
        ('student', 'Student'),
        ('trainee', 'Trainee'),
        ('contractor', 'Contractor'),
        ('freelance', 'Freelance')], string='Employee Type')
    action_type = fields.Selection([
            ('region', 'Region'),
            ('dept', 'Department'),
            ('emp_type', 'Employee Type'),
            ('emp_manager', 'Employee Manager'),
            ], string='Action')
    # update employee manager
    manager_id = fields.Many2one('hr.employee', string='New Manager',
                                 domain=[('driver_uid', '=', False),('employee_status', '=', 'active')])

    def action_update_dept(self):
        for rec in self:
            emp_ids = self.env['hr.employee'].browse(self._context.get('active_ids'))
            emp_ids.write({'department_id':rec.department_id.id})
        return True
    
    def action_update_region(self):
        for rec in self:
            emp_ids = self.env['hr.employee'].browse(self._context.get('active_ids'))
            emp_ids.write({'region_id':rec.region_id.id})
    
    def action_update_emp_type(self):
        for rec in self:
            emp_ids = self.env['hr.employee'].browse(self._context.get('active_ids'))
            emp_ids.write({'employee_type':rec.employee_type})

    def action_update_manager(self):
        for rec in self:
            if self.env.context.get('active_model') and self.env.context.get('active_model') == 'hr.employee' \
            and self.env.context.get('active_ids') and rec.manager_id:
                employee_ids = self.env['hr.employee'].browse(self.env.context.get('active_ids'))
                employee_ids.write({'parent_id':rec.manager_id.id})
