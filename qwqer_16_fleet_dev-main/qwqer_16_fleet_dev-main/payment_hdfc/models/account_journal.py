# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountJournal(models.Model):
    """
    Modifying account journal model
    """
    _inherit = 'account.journal'

    bank_name = fields.Selection([('hdfc', 'HDFC'), ('other', 'Other')], string='Bank Name')
