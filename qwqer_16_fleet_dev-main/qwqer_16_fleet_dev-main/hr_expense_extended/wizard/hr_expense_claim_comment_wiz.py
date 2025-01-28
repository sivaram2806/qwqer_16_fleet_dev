# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError


class FTLUserActionHistory(models.TransientModel):
    _name = "hr.expense.claim.comment"
    _description = "Hr Expense Claim Comment"

    user_id = fields.Many2one('res.users')
    description = fields.Char(string="Comments")

    def action_post_user_comment(self):
        active_id = self.env.context.get('active_ids', [])
        active_model_id = self.env.context.get('active_model')
        function = self.env.context.get('function')

        if not active_id or not active_model_id:
            raise UserError(_('Active ID or Active Model ID is missing in context.'))

        record = self.env[active_model_id].browse(active_id)

        values = {
            'user_id': self.env.user.id,
            'description': self.description,
        }

        function_state_map = {
            'action_hr_expense_claim_send_for_approval': {'state': 'pending_approval',
                                                          'user_comment': self.description or None},
            'action_hr_expense_claim_mu_approve': {'state': 'mu_approved', 'mu_approved_by': self.env.user.id,
                                                   'mu_comment': self.description or None},
            'action_hr_expense_claim_finance_approve': {'finance_approved_by': self.env.user.id,
                                                        'finance_manager_comment': self.description or None,
                                                        'state': 'approved'},
            'action_hr_expense_claim_finance_approve_advance': {'finance_approved_by': self.env.user.id,
                                                                'finance_manager_comment': self.description or None,
                                                                'state': 'approved_without_advance'},
            'action_hr_expense_claim_complete': {'state': 'completed'},
            'action_hr_expense_claim_cancel': {'state': 'cancelled'},
        }

        if function in function_state_map:
            record.update(function_state_map[function])
        # elif function == 'action_hr_expense_claim_finance_approve':
        #     vals = {'finance_approved_by': self.env.user.id, 'finance_manager_comment': self.description or None}
        #     vals.update({'state': 'approved'})
        #     record.update(vals)
        # elif function == 'action_hr_expense_claim_finance_approve_advance':
        #     vals = {'finance_approved_by': self.env.user.id, 'finance_manager_comment': self.description or None}
        #     vals.update({'state': 'approved_without_advance'})
        #     record.update(vals)
        elif function == 'action_hr_expense_claim_rejected':
            state_transition_map = {
                'approved': 'mu_approved',
                'approved_without_advance': 'mu_approved',
                'mu_approved': 'pending_approval',
                'pending_approval': 'new'
            }
            if record.state in state_transition_map:
                record.write({'state': state_transition_map[record.state]})
        self.sudo().create(values)
        # self. log_user_comments(record)
        return True

    def log_user_comments(self, record):
        function_rep = {'action_hr_expense_claim_send_for_approval': 'Send For Approval',
                        'action_hr_expense_claim_mu_approve': 'Mu Approved',
                        'action_hr_expense_claim_finance_approve': 'Finance Approved',
                        'action_hr_expense_claim_finance_approve_advance': 'Finance Approved With Out Advance',
                        'action_hr_expense_claim_complete': 'Completed',
                        'action_hr_expense_claim_cancel': 'Cancelled', }
        msg = 'test'
        self.message_post(body=msg)
