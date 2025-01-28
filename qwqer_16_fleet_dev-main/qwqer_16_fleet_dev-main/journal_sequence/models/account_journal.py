# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    sequence_id = fields.Many2one('ir.sequence', string='Entry Sequence',
                                  help="This field contains the information related to the numbering of the"
                                       " journal entries of this journal.",
                                  copy=False)
    sequence_number_next = fields.Integer(string='Next Number',
                                          help='The next sequence number will be used for the next invoice.',
                                          compute='_compute_seq_number_next',
                                          inverse='_inverse_seq_number_next')
    refund_sequence_id = fields.Many2one('ir.sequence', string='Credit Note Entry Sequence',
                                         help="This field contains the information related to the "
                                              "numbering of the credit note entries of this journal.",
                                         copy=False)
    refund_sequence_number_next = fields.Integer(string='Credit Notes Next Number',
                                                 help='The next sequence number will be used for the next'
                                                      'credit note.',
                                                 compute='_compute_refund_seq_number_next',
                                                 inverse='_inverse_refund_seq_number_next')

    @api.depends('sequence_id.use_date_range', 'sequence_id.number_next_actual')
    def _compute_seq_number_next(self):
        for journal in self:
            if journal.sequence_id:
                sequence = journal.sequence_id._get_current_sequence()
                journal.sequence_number_next = sequence.number_next_actual
            else:
                journal.sequence_number_next = 1

    def _inverse_seq_number_next(self):
        for journal in self:
            if journal.sequence_id and journal.sequence_number_next:
                sequence = journal.sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.sequence_number_next

    @api.depends('refund_sequence_id.use_date_range', 'refund_sequence_id.number_next_actual')
    def _compute_refund_seq_number_next(self):
        for journal in self:
            if journal.refund_sequence_id and journal.refund_sequence:
                sequence = journal.refund_sequence_id._get_current_sequence()
                journal.refund_sequence_number_next = sequence.number_next_actual
            else:
                journal.refund_sequence_number_next = 1

    def _inverse_refund_seq_number_next(self):
        for journal in self:
            if journal.refund_sequence_id and journal.refund_sequence and journal.refund_sequence_number_next:
                sequence = journal.refund_sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.refund_sequence_number_next

    @api.constrains("refund_sequence_id", "sequence_id")
    def _check_journal_sequence(self):
        for journal in self:
            if journal.refund_sequence_id and journal.sequence_id and journal.refund_sequence_id == journal.sequence_id:
                raise ValidationError(_("On journal '%s', the same sequence is used as "
                                        "Entry Sequence and Credit Note Entry Sequence.")% journal.display_name)
            if journal.sequence_id and not journal.sequence_id.company_id:
                raise ValidationError(_("The company is not set on sequence '%s' configured on journal '%s'.")
                                      % (journal.sequence_id.display_name, journal.display_name))
            if journal.refund_sequence_id and not journal.refund_sequence_id.company_id:
                raise ValidationError(_("The company is not set on sequence '%s' configured as "
                                        "credit note sequence of journal '%s'.")
                                      % (journal.refund_sequence_id.display_name, journal.display_name))




