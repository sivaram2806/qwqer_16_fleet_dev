# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountJournal(models.Model):
    """
    Modifying account journal model
    """
    _inherit = 'account.journal'

    is_cashfree = fields.Boolean(string='Is Cashfree Journal?')
    is_bank_journal = fields.Boolean(string='Is Bank Journal?')
