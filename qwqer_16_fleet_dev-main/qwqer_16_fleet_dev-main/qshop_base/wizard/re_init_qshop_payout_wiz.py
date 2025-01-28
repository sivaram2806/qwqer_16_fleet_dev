# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import  ValidationError


class ReInitiateWiz(models.TransientModel):
    _name = "re.init.qshop.payout.wiz"
    _description = "ReInitiated Wizard"

    payout_ids = fields.Many2many('qshop.merchant.payout.lines', string="Reinitiated")

    @api.model
    def default_get(self, fields):
        res = super(ReInitiateWiz, self).default_get(fields)
        if self.env.context.get('active_model') == 'qshop.merchant.payout' and self.env.context.get('active_id', False):
            rec_id = self.env['qshop.merchant.payout'].browse(self.env.context['active_id'])
            if rec_id and rec_id.line_ids:
                payout_ids = rec_id.line_ids.filtered(
                    lambda r: r.payment_state == 'fail' and r.re_initiated == 'no'
                ).ids
                if not payout_ids:
                    raise ValidationError(_('No Failed line for ReInitiate'))
                res.update({'payout_ids': [(6, 0, payout_ids)]})
        return res

    def action_repayment(self):
        for rec in self:
            if self._context.get('active_model') == 'qshop.merchant.payout' and self._context.get('active_id', False):
                data = self.env['qshop.merchant.payout'].browse(self._context.get("active_id"))
                if data and rec.payout_ids:
                    list = []
                    for line in rec.payout_ids:
                        if line.re_initiated == 'no':
                            vals = {
                                'from_date': line.from_date,
                                'to_date': line.to_date,
                                'customer_id': line.customer_id.id,
                                'total_pay': line.total_pay,
                                'service_charge': line.service_charge,
                                'taxes': line.taxes,
                                'balance_amt': line.balance_amt,
                                'remarks': line.remarks,
                                'line_ids': [(6, 0, line.line_ids.ids)],
                            }
                            line.re_initiated = 'yes'
                            list.append((0, 0, vals))
                    if list:
                        str = "ReInitiated  from  %s." % (data.rec_name)
                        payout_id = self.env['qshop.merchant.payout'].sudo().create(
                            {'region_id': data.region_id.id, 'description': str, 'from_date': data.from_date,
                             'to_date': data.to_date, 'line_ids': list,
                             'approved_user_id': self.env.user.id, 'approve_date': datetime.today(), 'state': 'approve'
                             })
                        for payout_line in payout_id.line_ids:
                            for trans_line in payout_line.line_ids:
                                trans_line.qshop_merchant_payout_id = payout_id.id
                        return {
                            'name': _('Qshop Merchant Payouts'),
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'qshop.merchant.payout',
                            'view_id': False,
                            'type': 'ir.actions.act_window',
                            'res_id': payout_id.id,
                        }
