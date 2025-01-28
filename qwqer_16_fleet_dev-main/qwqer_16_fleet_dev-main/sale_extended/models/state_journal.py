# -*- coding: utf-8 -*-
from odoo import models, fields


class StateJournal(models.Model):
    _inherit = 'state.journal'

    tax_b2c_invoice = fields.Many2many("account.tax", 'account_tax_state_journal_inv_rel', 'inv_state_journal_id', 'inv_tax_id',
                                       string='Tax - B2C Invoice')
    tax_b2c_sale_order = fields.Many2many("account.tax", 'account_tax_state_journal_so_rel', 'so_state_journal_id', 'so_tax_id',
                                          string='Tax - B2C Sale Order')