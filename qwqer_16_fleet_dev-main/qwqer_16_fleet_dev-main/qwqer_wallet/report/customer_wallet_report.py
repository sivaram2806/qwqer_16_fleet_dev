# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api


class CustomerWalletReport(models.Model):
    _name = "customer.wallet.report"
    _description = "Customer Wallet Report"
    _auto = False
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', index=True)
    debit_amt = fields.Float('Debit')
    credit_amt = fields.Float("Credit")
    wallet_balance = fields.Float("Wallet Balance")
    region_id = fields.Many2one(comodel_name='sales.region', string='Region', index=True)
    customer_type = fields.Selection(selection=[('b2c', 'B2C'), ('b2b', 'B2B')], string='Customer Type')
    wallet_id = fields.Integer("Wallet ID")
    service_type_id = fields.Many2one(comodel_name='partner.service.type', string="Customer Service Type")
    phone_number = fields.Char(string="Phone No.")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW customer_wallet_report AS (
                SELECT 
                    row_number() OVER() AS id,
                    RES.id AS partner_id,
                    RES.region_id AS region_id,
                    RES.wallet_id AS wallet_id, 
                    RES.customer_type AS customer_type,
                    RES.service_type_id AS service_type_id,
                    RES.phone AS phone_number,
                    SUM(AML_subquery.debit) AS debit_amt,
                    SUM(AML_subquery.credit) AS credit_amt, 
                    SUM(AML_subquery.balance) * -1 AS wallet_balance
                FROM 
                    res_partner AS RES
                    JOIN (
                        SELECT 
                            partner_id, 
                            debit, 
                            credit, 
                            balance
                        FROM 
                            account_move_line
                        WHERE 
                            parent_state != 'cancel'
                            AND journal_id = (
                                SELECT journal_id FROM customer_wallet_config LIMIT 1
                            )
                            AND account_id = (
                                SELECT default_credit_account_id 
                                FROM customer_wallet_config LIMIT 1
                            )
                    ) AS AML_subquery 
                    ON RES.id = AML_subquery.partner_id
                GROUP BY 
                    RES.id, 
                    RES.region_id, 
                    RES.wallet_id, 
                    RES.customer_type, 
                    RES.service_type_id, 
                    RES.phone
            );
        """)

    def action_wallet_details(self):
        """ Wallet transaction details for the selected customer
        """
        if self.partner_id:
            action = self.partner_id.action_customer_wallet_details()
            return action

