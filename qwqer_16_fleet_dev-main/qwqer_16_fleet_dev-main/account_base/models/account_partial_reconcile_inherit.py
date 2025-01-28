# -*- coding: utf-8 -*-
import logging
from odoo import models
from odoo.tools.sql import create_index

_logger = logging.getLogger(__name__)


class AccountMoveInherit(models.Model):
    _inherit = 'account.partial.reconcile'

    def init(self):
        """-- Max Date Index -- and -- Max Date, Full Reconcile Id Index --"""
        create_index(self._cr, 'account_partial_reconcile_max_date_index', 'account_partial_reconcile', ["max_date"])
        create_index(self._cr, 'account_partial_reconcile_max_date_full_reconcile_id_index',
                     'account_partial_reconcile', ["max_date", 'full_reconcile_id'])
        super().init()
