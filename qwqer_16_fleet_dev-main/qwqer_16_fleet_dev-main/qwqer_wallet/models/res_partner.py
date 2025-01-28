# -*- coding: utf-8 -*-

from odoo import api, models, fields,_
from datetime import date

from dateutil.relativedelta import relativedelta


class Partner(models.Model):
    _inherit = 'res.partner'


    wallet_id = fields.Integer("Wallet ID",store=True, index = True)
    is_wallet_active = fields.Boolean("Is Wallet Active")
    wallet_balance = fields.Float(string='Wallet Amount',compute='_compute_balance')

    def action_activate_wallet(self):
        for rec in self:
            rec.is_wallet_active = True
            rec.wallet_id = rec.customer_ref_key

    def action_deactivate_wallet(self):
        for rec in self:
            rec.is_wallet_active = False
            rec.wallet_id = 0

    def _compute_balance(self):
        for rec in self:
            wallet_config = self.env['customer.wallet.config'].search([('company_id','=',self.env.company.id)],limit=1)
            balance = self.compute_wallet_balance(rec,wallet_config,fields.Date.context_today(self))
            rec.wallet_balance = balance


    @api.model
    def create(self, vals):
        res = super(Partner, self).create(vals)
        if res.wallet_id and res.customer_rank > 0:
            res.is_wallet_active = True
        return res


    def compute_wallet_balance(self,partner,wallet_config,start_date):
        domain = [('partner_id', '=', partner.id), ('journal_id', '=', wallet_config.journal_id.id),
            ('account_id', '=', wallet_config.default_credit_account_id.id),('parent_state','=','posted')]
        if start_date:
            domain.append(('create_date','<=',start_date))
        account_move_lines = self.env['account.move.line'].sudo().search_read(
            domain, ['debit', 'credit', 'balance']
        )

        # debit_sum = sum(line['debit'] for line in account_move_lines)
        # credit_sum = sum(line['credit'] for line in account_move_lines)
        balance_sum = sum(line['balance'] for line in account_move_lines)

        # Wallet balance (credit-based calculation)
        wallet_balance = balance_sum * -1
        return wallet_balance

    def action_customer_wallet_details(self):
        """ Wallet transaction details for the selected customer """
        self.ensure_one()
        action = self.env.ref('qwqer_wallet.action_customer_wallet_detailed_report').read()[0]

        # Parameterized SQL query to avoid SQL injection
        query = """
            CREATE OR REPLACE VIEW customer_wallet_detailed_report AS (
                SELECT 
                    row_number() OVER() AS id,
                    RES.id as partner_id, 
                    SUM(AML.debit) AS credit_amt, 
                    SUM(AML.credit) AS debit_amt, 
                    SUM(AML.balance) AS balance_amt, 
                    SUM(AML.balance) + COALESCE(
                        SUM(AML.balance) OVER(
                            PARTITION BY AML.partner_id 
                            ORDER BY AML.id 
                            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                        ), 0
                    ) AS wallet_balance, 
                    AML.create_date AS create_dt, 
                    AML.ref AS reference, 
                    AML.name AS label, 
                    AM.name AS move_name, 
                    AM.wallet_transaction_ref_id as wallet_transaction_ref_id, 
                    AML.wallet_order_id as wallet_order_id, 
                    AM.comments as comments, 
                    AM.order_transaction_no, 
                    RES.phone AS phone_number 
                FROM 
                    res_partner AS RES
                    JOIN account_move_line AS AML ON RES.id = AML.partner_id 
                    JOIN account_move AS AM ON AML.move_id = AM.id 
                WHERE 
                    AML.parent_state != 'cancel' 
                    AND AML.account_id != (
                        SELECT default_debit_account_id 
                            FROM customer_wallet_config 
                            LIMIT 1
                        )
                    AND AML.move_id IN (
                        SELECT move_id 
                        FROM account_move_line 
                        WHERE 
                            parent_state != 'cancel' 
                            AND account_id = (
                                SELECT default_debit_account_id 
                                    FROM customer_wallet_config 
                                    LIMIT 1
                                )
                            AND journal_id = (
                                SELECT journal_id 
                                FROM customer_wallet_config 
                                LIMIT 1
                            )
                        ORDER BY id
                    )
                    AND AML.partner_id = %s
                GROUP BY 
                    RES.id, 
                    AML.id, 
                    AM.id
            )
        """

        self.env.cr.execute(query, (self.id,))

        return action



