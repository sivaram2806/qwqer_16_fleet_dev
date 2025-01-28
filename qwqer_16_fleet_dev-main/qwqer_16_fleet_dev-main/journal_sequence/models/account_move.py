# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    name = fields.Char(compute="_compute_name_by_sequence")

    @api.depends("state", "journal_id", "date")
    def _compute_name_by_sequence(self):
        for move in self:
            if (move.state == "posted" and (not move.name or move.name == "/") and move.journal_id
                    and move.journal_id.sequence_id):
                if (move.move_type in ("out_refund", "in_refund") and move.journal_id.type in ("sale", "purchase")
                        and move.journal_id.refund_sequence and move.journal_id.refund_sequence_id):
                    seq = move.journal_id.refund_sequence_id
                else:
                    seq = move.journal_id.sequence_id
                move.name = seq.next_by_id(sequence_date=move.date)
            elif (move.state == "posted" and (not move.name or move.name == "/") and move.journal_id
                    and not move.journal_id.sequence_id):
                move._set_next_sequence()
            if not move.name:
                move.name = "/"

    def _constrains_date_sequence(self):
        return True

    def _set_next_sequence(self):
        """Overriding, to get the next sequence number"""
        self.ensure_one()
        if self.journal_id.sequence_id:
            sequence = self.journal_id.sequence_id and self.journal_id.sequence_id.next_by_id(sequence_date=self.date) or "/"

            self[self._sequence_field] = sequence if not self.reversed_entry_id else f"R{sequence}"
        else:
            super()._set_next_sequence()