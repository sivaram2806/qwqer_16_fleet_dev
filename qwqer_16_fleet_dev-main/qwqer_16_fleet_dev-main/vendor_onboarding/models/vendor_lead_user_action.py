# -*- coding: utf-8 -*-

from odoo import fields, models


class VendorLeadUserActionHistory(models.Model):
    """
    The model used for storing action history done by every users.
    """
    _name = "vendor.lead.user.action.history"
    _description = "Vendor Lead User Action History"

    description = fields.Char(string="Comments")
    action = fields.Char(string="Action")
    vendor_lead_id = fields.Many2one('vendor.lead')

    def action_user_comment(self):
        active_id = self.env.context.get('active_ids', [])
        record = self.env['vendor.lead'].browse(active_id)
        current_approved_users = record.approved_users or {}
        current_state = record.state

        context_mapping = {
            'from_send_for_approve': {
                'state': 'pending_approval',
                'template': 'vendor_onboarding.vendor_onboarding_send_for_approval_email_template',
                'email_values': {'from_send_for_approve': True},
                'action_performed':'Send for Approval'
            },
            'from_manager_approve': {
                'state': 'manager_approve',
                'approved_user': {'manager_approved_user_id': self.env.user.id},
                'template': 'vendor_onboarding.vendor_onboarding_manager_approved_email_template',
                'email_values': {'from_manager_approve': True},
                'action_performed':'Manager Approved'
            },
            'from_finance_approve': {
                'action': record.action_finance_approve,
                'template': 'vendor_onboarding.vendor_onboarding_finance_approved_email_template',
                'email_values': {'from_finance_approve': True},
                'action_performed':'Finance Approved'
            },
            'from_return': {
                'template': 'vendor_onboarding.vendor_onboarding_return_email_template',
                'email_values': {'body_content': self.description, 'from_return': True},
                'action_performed':'Returned'
            },
            'from_reject': {
                'state': 'reject',
                'template': 'vendor_onboarding.vendor_onboarding_rejection_email_template',
                'email_values': {'body_content': self.description, 'from_reject': True},
                'action_performed':'Rejected'
            },
        }

        for context_key, context_data in context_mapping.items():
            if self.env.context.get(context_key, False):
                template_id = self.env.ref(context_data['template'])
                email_values = context_data.get('email_values', {})
                if 'action' in context_data:
                    context_data['action']()
                    template_id.with_context(email_values).send_mail(record.id, email_values=None, force_send=True)
                else:
                    template_id.with_context(email_values).send_mail(record.id, email_values=None, force_send=True)
                    if 'state' in context_data:
                        current_state = context_data['state']
                        if 'approved_user' in context_data:
                            current_approved_users.update(context_data['approved_user'])

                    else:
                        state_transition_map = {
                            'manager_approve': 'pending_approval',
                            'pending_approval': 'new'
                        }
                        if record.state in state_transition_map:
                            current_state = state_transition_map[record.state]
                            if current_approved_users and current_approved_users.get('manager_approved_user_id', False):
                                current_approved_users.update({'manager_approved_user_id': False})
                    record.write({'state': current_state, 'approved_users': current_approved_users})
                self.write({'vendor_lead_id': record.id,'action':context_data['action_performed']})
                break
