# -*- coding: utf-8 -*-
from odoo import  models, api, _
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        payments = self._create_payments()
        vendor_payout = payments.reconciled_bill_ids.mapped('vendor_payout_id')
        if vendor_payout:
            vendor_payout.batch_payout_line_ids.write({"payment_state": "success"})
            vendor_payout.state = "complete"

        return payments
