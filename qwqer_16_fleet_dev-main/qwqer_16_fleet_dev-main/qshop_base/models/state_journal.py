# -*- coding: utf-8 -*-
from odoo import models, fields


class StateJournal(models.Model):
    _inherit = 'state.journal'

    qshop_journal_id = fields.Many2one('account.journal')
    qshop_tcs_tax_id=fields.Many2one('account.tax', string='Shop Merchant Payout TCS Tax')
