# -*- coding: utf-8 -*-
from odoo import models


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self):
        """ Function to make corresponding credit note to be e-invoiced automatically"""
        
        res = super(AccountMoveReversal, self).reverse_moves()
        # Fetching the move id
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        account_moves = []
        if active_ids:
            account_moves = self.env['account.move'].search([('reversed_entry_id', 'in', active_ids),
                                                             ('reversed_entry_id.einvoice_generated', '=',True),
                                                             ('einvoice_generated', '=', False),
                                                             ('move_type', 'in', ['out_invoice','out_refund']),
                                                             ('partner_id.vat', '!=', False)])

        for move in account_moves:
            move.action_einvoice_create()
        return res
