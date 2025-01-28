# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date


class VehicleContractActionHistoryWizard(models.TransientModel):
    """
    Transient model which helps in storing vehicle contract user action history
    """
    _name = 'vehicle.contract.action.history.wizard'

    comments = fields.Char(string='Comment')

    def action_post_user_comment(self):
        function_to_stage = {
            'action_sent_for_approval_comment': {'state':'send_for_approval','action':'Send for Approval',
                                                 'email_template':'fleet_extend.send_for_approval_ftl_contract_email_template',
                                                 'email_values': {'from_send_for_approval': True}
                                                 },
            'action_return_to_send_for_approval': {'state':'send_for_approval','action':'Returned',
                                                   'email_template':'fleet_extend.return_ftl_contract_email_template',
                                                   'email_values':{'body_content': self.comments,'from_return': True}
                                                   },
            'action_return_to_new': {'state':'new','action':'Returned',
                                     'email_template':'fleet_extend.return_ftl_contract_email_template',
                                     'email_values':{'body_content': self.comments,'from_return_to_new': True}
                                     },
            'action_mu_approve_comment': {'state':'mu_head_approved','action':'MU Approved',
                                          'email_template':'fleet_extend.rm_approve_ftl_contract_email_template',
                                          'email_values': {'from_mu_approve': True}
                                          },
            'action_finance_approve_comment': {'state':'','action':'Finance Approved',
                                               'email_template':'fleet_extend.finance_approve_ftl_contract_email_template',
                                               'email_values': {'from_finance_approve': True}
                                               },
            'action_close_contract_comment': {'state':'','action':'Closed',
                                              'email_template':'fleet_extend.close_ftl_contract_email_template',
                                              'email_values':{'body_content': self.comments,'from_close': True}
                                              },
            'action_run': {'state':'running','action':'Running',
                           'email_template':'fleet_extend.expiring_ftl_contract_email_template',
                           'email_values':{'subject': '','body_content': 'moved to Running','from_run': True}
                           },
        }

        function = self.env.context.get('function')
        if function in function_to_stage:
            active_id = self.env.context.get('active_ids', [])
            if not active_id:
                raise UserError(_('No active record found.'))

            record = self.env['vehicle.contract'].browse(active_id)

            if function == 'action_finance_approve_comment':
                approval_stage_updates = {'approval_stage': 'finance_approved'}

                if record.parent_id:
                    if record.parent_id.state == 'running':
                        record.write(approval_stage_updates)
                    elif record.start_date <= fields.Date.today():
                        approval_stage_updates['state'] = 'running'
                        record.write(approval_stage_updates)
                    else:
                        record.write(approval_stage_updates)
                else:
                    if record.start_date <= fields.date.today():
                        approval_stage_updates['state'] = 'running'
                    record.write(approval_stage_updates)

            elif function == 'action_close_contract_comment':
                if record.child_ids:
                    for child in record.child_ids:
                        if child.approval_stage == 'finance_approved':
                            if child.start_date <= fields.Date.today():
                                function_to_stage[function]['email_template'] = 'fleet_extend.running_ftl_contract_email_template'
                                function_to_stage[function]['email_values'] = {'body_content': f'Contract {record.contract_num} has been closed',
                                                                               'child_contract':child.contract_num,
                                                                               'reason': self.comments,'from_run': True}
                                child.write({'state': 'running'})
                                record.write({'state': 'closed'})
                            else:
                                record.write({'state': 'closed'})
                else:
                    record.write({'state': 'closed'})

            elif function == 'action_run':
                self.acton_run_contract(record)

            template_id = self.env.ref(function_to_stage[function]['email_template'])
            if 'subject' in function_to_stage[function]['email_values']:
                function_to_stage[function]['email_values']['subject'] = f'Contract {record.contract_num} moved to Running'
            email_values = function_to_stage[function]['email_values']
            template_id.with_context(email_values).send_mail(record.id, email_values=None, force_send=True)

            values = {
                'user_id': self.env.user.id,
                'action': function_to_stage[function]['action'],
                'description': self.comments,
                'vehicle_contract_id': record.id,
                'last_updated_on': fields.datetime.today()
            }
            self.env['vehicle.contract.action.history'].create(values)

            approval_stage = (function_to_stage.get(function)).get('state')
            if approval_stage in ['new', 'send_for_approval', 'mu_head_approved', 'finance_approved']:
                record.approval_stage = approval_stage
            elif approval_stage in ['running', 'expired', 'closed']:
                record.state = approval_stage

    def acton_run_contract(self, record):
        if record.parent_id:
            running_child = self.env['vehicle.contract'].search(
                [('parent_id', '=', record.parent_id.id), ('state', '=', 'running')])
            if record.parent_id.state == 'running':
                raise UserError(_('Parent contract is in running state.'))
            elif running_child:
                raise UserError(
                    _("Contract %s is running. Please close that contract!" % ', '.join(
                        con_id.contract_num for con_id in running_child))
                )
        today = date.today()
        if record.start_date > today:
            raise UserError(
                _("Can't change Contract status to running before %s!" % record.start_date))
        record.write({'state': 'running', 'start_date': fields.datetime.today()})
