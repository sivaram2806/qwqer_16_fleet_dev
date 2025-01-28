# -*- coding: utf-8 -*-

from odoo import fields, models, _


class UserActionCommentWizard(models.TransientModel):
    """The Transient model used for saving the comments and sending mail."""
    _name = 'user.action.comment.wizard'

    comments = fields.Char()

    def action_user_comment(self):
        active_id = self.env.context.get('active_ids', [])
        record = self.env['batch.trip.uh'].browse(active_id)

        values = {
            'description': self.comments,
            'batch_trip_uh_id': record.id,
        }

        context_mapping = {
            'from_send_for_approve': {
                'action': record.action_send_for_approval,
                'action_performed':'Send for Approval',
                'template': 'fleet_urban_haul.batch_trip_uh_send_for_approval_email_template',
            },
            'from_approve': {
                'action': record.action_approved,
                'action_performed':'Approved',
                'template': 'fleet_urban_haul.batch_trip_uh_approved_email_template',
            },
            'from_return': {
                'action': record.action_return,
                'action_performed':'Returned',
                'template': 'fleet_urban_haul.batch_trip_uh_returned_email_template',
                'email_values': {'body_content': self.comments},
            },
            'from_reject': {
                'action': record.action_rejected,
                'action_performed':'Rejected',
                'template': 'fleet_urban_haul.batch_trip_uh_rejected_email_template',
                'email_values': {'body_content': self.comments},
            },
        }

        for context_key, context_data in context_mapping.items():
            if self.env.context.get(context_key, False):
                context_data['action']()
                values['action'] = context_data['action_performed']
                self.env['user.action.history'].create(values)
                template_id = self.env.ref(context_data['template'])
                email_values = context_data.get('email_values', {})
                template_id.with_context(email_values).send_mail(record.id, email_values=None, force_send=True)
                break



