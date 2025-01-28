# -*- coding: utf-8 -*-

from odoo import fields, models


class HrEmployeeUpdateWizardExtended(models.TransientModel):
    _inherit = 'hr.employee.update.wizard'
    _description = "Update expense manager in bulk for employees"

    def get_user_expense_approver(self):
        manager_group = self.env.ref('hr_expense.group_hr_expense_team_approver', raise_if_not_found=False)
        emp_rec = self.env['hr.employee'].search([('user_id','in',manager_group.users.ids)])
        return [('id', 'in', list(emp_rec.ids)),('driver_uid','=', False),('employee_status','=','active')]

    action_type = fields.Selection(selection_add=[('expense_mngr', 'Expense Manager Update')])
    expense_hr_manager_id = fields.Many2one('hr.employee',
                                                string="New Manage", domain=get_user_expense_approver)

    def update_expense_manager(self):
        if self.expense_hr_manager_id and self.env.context.get('active_ids'):
            employee_ids = self.env['hr.employee'].browse(self.env.context.get('active_ids'))
            for employee in employee_ids:
                employee.expense_manager_id = self.expense_hr_manager_id.user_id.id or False
            
                
