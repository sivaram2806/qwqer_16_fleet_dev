from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import Warning, UserError, RedirectWarning, ValidationError


class ReInitiatePaymentWiz(models.TransientModel):
    _name = "reinitiate.payment.wiz"
    _description = "Reinitiated Wizard"

    @api.model
    def default_get(self, fields):
        res = super(ReInitiatePaymentWiz, self).default_get(fields)
        if self._context.get('active_model') == 'driver.batch.payout' and self._context.get('active_id', False):
            rec_id = self.env['driver.batch.payout'].browse(self._context.get("active_id"))

            if rec_id and rec_id.batch_payout_line_ids:
                res.update({'payout_ids': [(6,0, rec_id.batch_payout_line_ids.filtered(
                    lambda r: r.payment_state == 'fail' and r.is_reinitiated == 'no').ids)],
                            })
        return res

    payout_ids = fields.Many2many('driver.batch.payout.lines', 'payout_repayment_rel', 'line_id', 'wiz_id',
                                  string="Reinitiated")

    def action_repayment(self):
        for rec in self:
            if self._context.get('active_model') == 'driver.batch.payout' and self._context.get('active_id', False):
                batch_payout = self.env['driver.batch.payout'].browse(self._context.get("active_id"))
                if batch_payout and rec.payout_ids:
                    list = []
                    for line in rec.payout_ids:
                        if line.is_reinitiated == 'no':
                            vals = {
                                'from_date': line.from_date,
                                'to_date': line.to_date,
                                'employee_id': line.employee_id.id,
                                'daily_payout_amount': line.daily_payout_amount,
                                'incentive_amount': line.incentive_amount,
                                'deduction_amount': line.deduction_amount,
                                'remarks': line.remarks,
                                'daily_payout_ids': [(6, 0, line.daily_payout_ids.ids)],
                            }
                            line.is_reinitiated = 'yes'
                            list.append((0, 0, vals))
                    if list:
                        str = "Reinitiated  from  %s." % (batch_payout.name)
                        payout_id = self.env['driver.batch.payout'].sudo().create(
                            {'region_id': batch_payout.region_id.id, 'description': str, 'from_date': batch_payout.from_date,
                             'to_date': batch_payout.to_date, 'batch_payout_line_ids': list, 'state': 'verify'
                             })
                        for payout_line in payout_id.batch_payout_line_ids:
                            for daily_trans_line in payout_line.daily_payout_ids:
                                daily_trans_line.batch_payout_id = payout_id.id

                        return {
                            'name': _('Weekly/Monthly Payouts'),
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'driver.batch.payout',
                            'view_id': False,
                            'type': 'ir.actions.act_window',
                            'res_id': payout_id.id,
                        }
