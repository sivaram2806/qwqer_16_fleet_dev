# -*- coding: utf-8 -*-

from odoo import models, fields

class PaymentMode(models.Model):
    _inherit = 'payment.mode'

    is_wallet_payment = fields.Boolean("Is a Wallet Payment Mode")