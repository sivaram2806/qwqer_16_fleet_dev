# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class WOAdvPaymentWiz(models.TransientModel):
    """
    Wizard to get and payment information and create a payment in account.payment
    """
    _inherit = 'wo.adv.payment.wizard'


    def action_post_payment(self, payment_obj):
        if payment_obj:
            if self.journal_id.bank_name != 'hdfc':
                payment_obj.action_post()
            else:
                payment_obj.move_id._set_next_sequence()