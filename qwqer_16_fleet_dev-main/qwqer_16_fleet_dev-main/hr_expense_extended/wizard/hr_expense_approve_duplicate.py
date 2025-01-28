# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrExpenseApproveDuplicateExtend(models.TransientModel):
    """
    This wizard is shown whenever an approved expense is similar to one being
    approved. The user has the opportunity to still validate it or decline.
    """

    _inherit = "hr.expense.approve.duplicate"

    def action_approve(self):
        self.sheet_ids._do_approve()
        if self.env.context.get('active_model') == 'hr.expense.claim':
            self.sheet_ids.action_sheet_move_create()
