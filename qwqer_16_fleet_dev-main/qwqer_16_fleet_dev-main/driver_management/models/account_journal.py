# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountJournal(models.Model):
    """
    Modifying account journal model
    """
    _inherit = 'account.journal'

    is_driver_journal = fields.Boolean(string='Is Driver Journal?')
