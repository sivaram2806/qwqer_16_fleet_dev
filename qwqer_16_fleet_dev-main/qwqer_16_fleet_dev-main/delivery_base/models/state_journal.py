# -*- coding: utf-8 -*-
from odoo import models, fields


class StateJournal(models.Model):
    _inherit = 'state.journal'

    delivery_journal_id = fields.Many2one('account.journal')