# -*- coding: utf-8 -*-

from odoo import models, api

class CustomerBalance(models.Model):
    _inherit = 'customer.balance'
    _description = 'Customer Balance'

    @api.model
    def _sum_bal_amount(self):
        rec = super()._sum_bal_amount()
        rec += '''- COALESCE(WAL.wallet_balance, 0.00)'''
        return rec

    @api.model
    def _select(self):
        rec = super()._select()
        rec += ''',
        COALESCE(WAL.wallet_balance, 0.00) AS wallet_balance'''
        return rec

    @api.model
    def _from(self):
        rec = super()._from()
        rec+='''
        LEFT JOIN (
            SELECT
                aml.partner_id AS partner_id,
                SUM(aml.balance) * -1 AS wallet_balance
            FROM
                account_move_line aml
            WHERE
                aml.parent_state = 'posted'
                AND aml.partner_id IS NOT NULL
                AND aml.account_id = (
                    SELECT default_debit_account_id
                        FROM customer_wallet_config
                        LIMIT 1
                )
                AND aml.journal_id = (
                    SELECT journal_id
                    FROM customer_wallet_config
                    LIMIT 1
                )
            GROUP BY
                aml.partner_id) WAL ON rp.id = WAL.partner_id'''
        return rec