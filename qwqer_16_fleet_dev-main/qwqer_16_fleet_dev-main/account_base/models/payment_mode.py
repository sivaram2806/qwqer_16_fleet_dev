# -*- coding: utf-8 -*-
from odoo import fields, models, api


class PaymentMode(models.Model):
    """For adding payment modes for orders"""
    _name = 'payment.mode'
    _description = 'Payment Mode'

    name = fields.Char(string='Payment Mode')
    code = fields.Char(string='Code')
    is_credit_payment = fields.Boolean("Is a Credit Payment Mode")
    journal_id = fields.Many2one(comodel_name="account.journal", string='Journal')