# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

from odoo.exceptions import ValidationError, UserError


class AccountMoveInherit(models.Model):
    """ The model account_move is inherited to make modifications """
    _inherit = 'account.move'

    vehicle_customer_consolidate_id = fields.Many2one('trip.summary.uh', string='Vehicle Consolidated No.',
                                                      copy=False)

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state')
    def _compute_amount(self):
        res = super(AccountMoveInherit, self)._compute_amount()
        for rec in self:
            if rec.vehicle_customer_consolidate_id:
                if rec.vehicle_customer_consolidate_id.invoice_id.state == "posted":
                    rec.vehicle_customer_consolidate_id.state = "paid"
        return res

    def action_post(self):
        for rec in self:
            res = super(AccountMoveInherit, self).action_post()

            if rec.vehicle_customer_consolidate_id:
                rec.vehicle_customer_consolidate_id.state = 'posted'

            return res

    def button_draft(self):
        for rec in self:
            if rec.vehicle_customer_consolidate_id:
                if rec.state == 'cancel':
                    raise UserError(
                        _("Reset to draft is restricted in cancelled consolidated invoice. Please create a new consolidated invoice"))
                else:
                    rec.vehicle_customer_consolidate_id.state = 'draft'
                    if rec.vehicle_customer_consolidate_id.partner_type == 'customer':
                        daily_trip_line_ids = self.env['batch.trip.uh.line'].search(
                            [('batch_trip_uh_id', '!=', False), (
                                'trip_summary_customer_id', '=', rec.vehicle_customer_consolidate_id.id)])
                        daily_trip_line_ids.mapped('batch_trip_uh_id').write({'state': 'approved'})
                    else:
                        daily_trip_line_ids = self.env['batch.trip.uh.line'].search(
                            [('batch_trip_uh_id', '!=', False), (
                                'trip_summary_vendor_id', '=', rec.vehicle_customer_consolidate_id.id)])
                        daily_trip_line_ids.mapped('batch_trip_uh_id').write({'state': 'approved'})
            return super(AccountMoveInherit, self).button_draft()

    def button_cancel(self):
        for rec in self:
            res = super(AccountMoveInherit, self).button_cancel()
            if rec.vehicle_customer_consolidate_id:
                rec.vehicle_customer_consolidate_id.state = 'cancelled'
                if rec.vehicle_customer_consolidate_id.partner_type == 'customer':
                    daily_trip_line_ids = self.env['batch.trip.uh.line'].search([('batch_trip_uh_id', '!=', False), (
                        'trip_summary_customer_id', '=', rec.vehicle_customer_consolidate_id.id)])
                    # daily_trip_line_ids.mapped('batch_trip_uh_id').write({'invoice_state': 'to_invoice'})
                    daily_trip_line_ids.write({'trip_summary_customer_id': False,
                                               'invoice_state': 'to_invoice'})
                else:
                    daily_trip_line_ids = self.env['batch.trip.uh.line'].search([('batch_trip_uh_id', '!=', False), (
                        'trip_summary_vendor_id', '=', rec.vehicle_customer_consolidate_id.id)])
                    daily_trip_line_ids.write({'trip_summary_vendor_id': False, 'bill_state': 'to_paid'})
            return res

    def unlink(self):
        for rec in self:

            if rec.vehicle_customer_consolidate_id:
                if rec.state != 'cancel':
                    rec.vehicle_customer_consolidate_id.state = 'new'

            return super(AccountMoveInherit, self).unlink()

