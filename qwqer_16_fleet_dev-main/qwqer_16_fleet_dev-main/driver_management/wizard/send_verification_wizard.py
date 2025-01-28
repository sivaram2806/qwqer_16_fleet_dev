from odoo import api, fields, models, _


class SendVerificationWizard(models.TransientModel):
    _name = "send.verification.wizard"

    message = fields.Text('Message')

    def send_for_verify_action(self):
        for rec in self:
            payout_id = self.env['driver.batch.payout'].browse(self._context.get('active_id'))
            if payout_id:
                if self.env.context.get('verify'):
                    payout_id.update_verify()
                else:
                    payout_id.update_ready_to_verify()