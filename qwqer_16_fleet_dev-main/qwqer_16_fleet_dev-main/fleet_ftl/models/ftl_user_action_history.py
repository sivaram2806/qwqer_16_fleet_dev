# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError


class FTLUserActionHistory(models.Model):
    _name = "ftl.user.action.history"
    _description = "FTL User Action History"

    user_id = fields.Many2one('res.users')
    description = fields.Char(string="Comments")
    last_updated_on = fields.Datetime(string="Time of Action")
    work_order_id = fields.Many2one('work.order')
    batch_trip_ftl_id = fields.Many2one('batch.trip.ftl')
    action = fields.Char(string="Action Performed")

    def action_post_user_comment(self):
        active_id = self.env.context.get('active_ids', [])
        active_model_id = self.env.context.get('active_model')
        current_state = self.env.context.get('current_state')
        function = self.env.context.get('function')

        if not active_id or not active_model_id:
            raise UserError(_('Active ID or Active Model ID is missing in context.'))

        record = self.env[active_model_id].browse(active_id)

        values = {
            'user_id': self.env.user.id,
            'description': self.description,
            'work_order_id': record.id if active_model_id == 'work.order' else False,
            'batch_trip_ftl_id': record.id if active_model_id == 'batch.trip.ftl' else False,
            'last_updated_on': fields.datetime.today()
        }

        function_state_map = {
            'action_sent_for_approval_ftl_wo': {'state':'pending_approval','action':'Send for Approval',
                                                'email_template':'fleet_ftl.work_order_send_for_approval_email_template',
                                                'email_values': {'from_send_for_approve': True}
                                                },
            'action_mu_approve_ftl_wo': {'state':'mu_approve','action':'MU Approved',
                                         'email_template':'fleet_ftl.work_order_mu_approved_email_template',
                                        'email_values': {'from_mu_approve': True}
                                        },
            'action_finance_approve_ftl_wo': {'state':'finance_approve','action':'Finance Approved',
                                              'email_template':'fleet_ftl.work_order_finance_approved_email_template',
                                              'email_values': {'from_finance_approve': True}
                                              },
            'action_reject_ftl_wo': {'state':'rejected','action':'Rejected',
                                     'email_template':'fleet_ftl.work_order_reject_email_template',
                                     'email_values':{'body_content': self.description,'from_reject': True}
                                     },
            'action_ftl_send_for_approval_ftl_batch_trip': {'state':'pending_approval','action':'Send for Approval',
                                                            'email_template':'fleet_ftl.batch_trip_ftl_send_for_approval_email_template',
                                                            'email_values': {'from_send_for_approve': True}
                                                            },
            'action_ftl_trip_finance_approve_ftl_batch_trip': {'state':'finance_approved','action':'Finance Approved',
                                                               'email_template':'fleet_ftl.batch_trip_ftl_finance_approved_email_template',
                                                               'email_values': {'from_finance_approve': True}
                                                               },
            'action_ftl_ops_approve_ftl_batch_trip': {'state':'ops_approved','action':'Ops Approved',
                                                      'email_template':'fleet_ftl.batch_trip_ftl_ops_approved_email_template',
                                                      'email_values': {'from_ops_approve': True}
                                                      },
            'action_ftl_trip_complete_ftl_batch_trip': {'state':'completed','action':'Completed',
                                                        'email_template':'fleet_ftl.batch_trip_ftl_completed_email_template',
                                                        'email_values': {'from_trip_complete': True}
                                                        },
            'action_ftl_trip_rejected_ftl_batch_trip': {'state':'rejected','action':'Rejected',
                                                        'email_template':'fleet_ftl.batch_trip_ftl_rejected_email_template',
                                                        'email_values':{'body_content': self.description,'from_reject': True}
                                                        },
            'action_ftl_return_ftl_batch_trip': {'state':'','action':'Returned',
                                                 'email_template':'fleet_ftl.batch_trip_ftl_returned_email_template',
                                                'email_values':{'body_content': self.description,'from_return': True}
                                                },
        }

        if function in function_state_map:
            template_id = self.env.ref(function_state_map[function]['email_template'])
            email_values = function_state_map[function]['email_values']
            template_id.with_context(email_values).send_mail(record.id, email_values=None, force_send=True)
            record.update({'state': function_state_map[function]['state']})

            if function == 'action_ftl_trip_rejected_ftl_batch_trip':
                record.write({'invoice_state': "nothing_to_invoice"})

            if function == 'action_ftl_return_ftl_batch_trip':
                state_transition_map = {
                    'finance_approved': 'ops_approved',
                    'ops_approved': 'pending_approval',
                    'pending_approval': 'new'
                }
                if current_state in state_transition_map:
                    record.write({'state': state_transition_map[current_state]})

            values['action'] = function_state_map[function]['action']
            self.sudo().create(values)
            return True

        if function == 'action_return_ftl_wo':
            template_id = self.env.ref('fleet_ftl.work_order_return_email_template')
            email_values = {'body_content': self.description, 'from_return': True}
            template_id.with_context(email_values).send_mail(record.id, email_values=None, force_send=True)
            state_transition_map = {
                'finance_approve': 'mu_approve',
                'mu_approve': 'pending_approval',
                'pending_approval': 'new'
            }
            if record.state in state_transition_map:
                record.write({'state': state_transition_map[record.state]})
                values['action'] = 'Returned'
                self.sudo().create(values)
                return True

        return False
