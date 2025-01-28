from odoo import api,fields, models,_
from odoo.exceptions import ValidationError,UserError


class BulkTripApproveWizard(models.TransientModel):
    """The Transient model used for approving bulk urban haul trips."""
    _name = "bulk.trip.approve.wizard"

    mail_approval_received = fields.Selection([
                              ("yes","Yes"),
                              ("no","No")], default="no", string='Mail Approval Received?')
    comments = fields.Text(string='Comments')
    attachment = fields.Binary(string='Attachment')
    attachment_name = fields.Char(string='Attachment Name')

    def bulk_approve_daily_trip(self):
        """
        Method to change the state to approved when selected multiple urban haul trips.
        """
        active_id_list = self.env.context.get('active_ids')
        active_records = self.env['batch.trip.uh'].browse(active_id_list)
        for record in active_records:
            if self.mail_approval_received == 'yes':
                if record.state == 'pending_approval':
                    values = {
                        'description': self.comments,
                        }
                    record.write({'mail_approval_received': self.mail_approval_received,
                                  'state': 'approved',
                                  'approved_attachment': self.attachment,
                                  'attachment_name': self.attachment_name,
                                  'approved_user_id': self.env.user.id,
                                  'user_action_ids': [(0, 0, values)]})
                    record.action_approved()
                else:
                    raise UserError(_('Please select only pending approvals from daily trips'))
            else:
                raise UserError(_('Confirmation email required'))

