# -*- coding: utf-8 -*-
from odoo import models, fields,api,_
from odoo.exceptions import ValidationError,UserError
import logging

_logger = logging.getLogger(__name__)


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    driver_id = fields.Many2one('hr.employee', string='Driver')
    vendor_payout_id = fields.Many2one('driver.batch.payout', string='Vendor Payout', copy=False)

    # def write(self, vals):
    #     res = super(AccountMoveInherit, self).write(vals)
    #     for rec in self:
    #         try:
    #             # Update driver id for move lines
    #             driver_id = rec.env['hr.employee'].search([('related_partner_id', '=', rec.partner_id.id)])
    #             if driver_id:
    #                 rec.driver_id = driver_id.id
    #         except Exception as e:
    #             _logger.exception(str(e))
    #     return res

    def button_draft(self):
        for rec in self:

            if rec.vendor_payout_id:

                if rec.state == 'cancel':
                    raise UserError(
                        _("Reset to draft is restricted in cancelled payout bill. Please create a new payout"))

                else:
                    rec.vendor_payout_id.state = 'pending'
                    rec.vendor_payout_id.batch_payout_line_ids.write({"payment_state": "pending"})

            return super().button_draft()

    def button_cancel(self):
        for rec in self:
            res = super().button_cancel()

            if rec.vendor_payout_id:
                rec.vendor_payout_id.state = 'cancel'
                rec.vendor_payout_id.batch_payout_line_ids.write({"payment_state": "fail"})
                driver_payouts = self.env['driver.payout'].search([('batch_payout_id', '=', rec.vendor_payout_id.id)])
                driver_payouts.write({'batch_payout_id': False})
                rec.vendor_payout_id.deduction_entry_id.button_draft()
                rec.vendor_payout_id.deduction_entry_id.button_cancel()
                rec.vendor_payout_id.deduction_entry_id = False

            return res

    def unlink(self):
        for rec in self:

            if rec.vendor_payout_id:
                if rec.state != 'cancel':
                    rec.vendor_payout_id.state = 'approve'
                    rec.vendor_payout_id.batch_payout_line_ids.write({"payment_state": "initiate"})
                    rec.vendor_payout_id.deduction_entry_id.button_draft()
                    rec.vendor_payout_id.deduction_entry_id.button_cancel()
                    rec.vendor_payout_id.deduction_entry_id = False
            return super().unlink()

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state')
    def _compute_amount(self):
        res = super()._compute_amount()

        for rec in self:
            if rec.vendor_payout_id:
                if rec.payment_state == "paid" and rec.state == "posted":
                    rec.vendor_payout_id.batch_payout_line_ids.write({"payment_state": "success"})
                    rec.vendor_payout_id.state = "complete"

        return res

