# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    utr_ref = fields.Char(string='UTR Reference')

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        # validate if the records in lines with different product hsn code in line
        if self.env.context.get('from_fleet', False) or self.env.context.get('invoice_form', False):
            for rec in res:
                hsn_code = len(set(rec.invoice_line_ids.mapped('product_id.l10n_in_hsn_code')))
                if hsn_code > 1:
                    raise UserError(_('Please not select different hsn code product!!!'))
        return res

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        # validate if the records in lines with different product hsn code in line
        if self.env.context.get('from_fleet', False) or self.env.context.get('invoice_form', False):
            for rec in self:
                hsn_code = len(set(rec.invoice_line_ids.mapped('product_id.l10n_in_hsn_code')))
                if hsn_code > 1:
                    raise UserError(_('Please not select different hsn code product!!!'))

        return res

    def action_register_payment(self):
        """extended to validate if UTR Reference Number is added on 'in_invoice', 'in_refund'"""
        for rec in self:
            if rec.vehicle_customer_consolidate_id and rec.move_type in ('in_invoice', 'in_refund') and not rec.utr_ref:
                raise UserError(_("Please fill UTR Reference Number."))
            else:
                return super(AccountMove, self).action_register_payment()
