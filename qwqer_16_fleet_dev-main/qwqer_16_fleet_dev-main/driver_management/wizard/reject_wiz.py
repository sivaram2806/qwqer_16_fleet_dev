# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2021 ZestyBeanz Technologies Pvt. Ltd.
#    (http://wwww.zbeanztech.com)
#    contact@zbeanztech.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models, _
from datetime import datetime,timedelta,date
from odoo.exceptions import Warning, UserError, RedirectWarning, ValidationError



class RejectReasonWiz(models.TransientModel):
    _name = "reject.reason.wiz"
    _description = "Reject Reason Wizard"
    
    
    reject_reason = fields.Text("Description")
    
    
    def update_reason(self):
        for rec in self:
            payout_id = self.env['driver.batch.payout'].browse(self._context.get('active_id', []))
            if payout_id:
                if payout_id.state in ('approve','verify'):
                    for line in payout_id.batch_payout_line_ids:
                        if line.payable_journal_id:
                           line.payable_journal_id.button_cancel()
                           line.payable_journal_id=False  
                    payout_id.state = "draft"
                    payout_id.is_reject=True
                    tracking = self.env['mail.tracking.value'].search([
                        ('field.name', '=', 'state'),  # The field being tracked
                        ('new_value_char', '=', 'Verified'),  # New value is 'Verified'
                        ('mail_message_id.res_id', '=', payout_id.id),
                        ('mail_message_id.model', '=', payout_id._name)
                    ], limit=1, order='create_date desc')
                    payout_verified_user=tracking.create_uid
                    if payout_verified_user:
                        template_id = self.env.ref('driver_management.rejection_email_template_driver_payouts').id
                        template = self.env['mail.template'].browse(template_id)
                        template.email_to = payout_verified_user.email
                        template.send_mail(payout_id.id, force_send=True)
                    message = f"<b>Batch Transfer Reject<b/><br/>Reason: {self.reject_reason}"
                    payout_id.message_post(body=message,message_type='comment')
                else:
                    state = payout_id.state and dict(payout_id._fields['state'].selection).get(payout_id.state) or ''
                    raise UserError(_('%s rejection is restricted.Payout is already  in %s status.Please Refresh!'%(payout_id.name,state))) 



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: