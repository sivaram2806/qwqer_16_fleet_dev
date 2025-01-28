# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api
import logging

_logger = logging.getLogger(__name__)

class CustomerBalance(models.Model):
    _name = 'customer.balance'
    _description = 'Customer Balance'
    _auto = False
    _rec_name = "partner_id"

    partner_id = fields.Many2one('res.partner', string='Partner')
    cus_id = fields.Integer("Customer ID")
    region_id = fields.Many2one(comodel_name='sales.region', string='Region')
    customer_type = fields.Selection([('b2c', 'B2C'), ('b2b', 'B2B')], string='Customer Type',default='b2b')
    service_type_id = fields.Many2one(comodel_name='partner.service.type')
    rev_balance = fields.Float("Receivable Balance", digits='Product Price')
    pay_balance = fields.Float("Payable Balance", digits='Product Price')
    wallet_balance = fields.Float("Wallet Balance", digits='Product Price')
    to_inv_so_total = fields.Float("Sale Order (To be Invoiced)", digits='Product Price')
    balance = fields.Float("Balance", digits='Product Price')

    @api.model
    def _sum_bal_amount(self):
        return ''',
        COALESCE(R.rev_balance, 0.00) + COALESCE(P.pay_balance, 0.00) + COALESCE(S.so_total, 0.00) + COALESCE(DAML.daml_balance, 0.00)'''

    @api.model
    def _select(self):
        return '''SELECT 
        rp.id AS id,
        rp.customer_ref_key AS cus_id,
        rp.id AS partner_id,
        rp.customer_type AS customer_type,
        rp.region_id AS region_id,
        rp.service_type_id AS service_type_id,
        COALESCE(R.rev_balance, 0.00) AS rev_balance,
        COALESCE(P.pay_balance, 0.00) AS pay_balance,
        COALESCE(S.so_total, 0.00) + COALESCE(DAML.daml_balance, 0.00) AS to_inv_so_total''' + '''%s''' % self._sum_bal_amount() + ''' as balance'''


    @api.model
    def _from(self):
        return '''FROM
        res_partner rp
        LEFT JOIN
            partner_service_type pst ON pst.id = rp.service_type_id
        LEFT JOIN (
            SELECT
                aml.partner_id AS partner_id,
                SUM(aml.balance) AS rev_balance
            FROM
                account_move_line aml
            JOIN
                account_account aa ON aa.id = aml.account_id
            WHERE
                aa.account_type = 'asset_receivable'
                AND aml.parent_state = 'posted'
                AND aml.partner_id IS NOT NULL
            GROUP BY
                aml.partner_id) R ON rp.id = R.partner_id
        LEFT JOIN (
            SELECT
                aml.partner_id AS partner_id,
                SUM(aml.balance) AS pay_balance
            FROM
                account_move_line aml
            JOIN
                account_account aa ON aa.id = aml.account_id
            WHERE
                aa.account_type  = 'liability_payable'
                AND aml.parent_state = 'posted'
                AND aml.partner_id IS NOT NULL
            GROUP BY
                aml.partner_id) P ON rp.id = P.partner_id
        LEFT JOIN (
            SELECT
                so.partner_id AS partner_id,
                SUM(so.amount_total) AS so_total
            FROM
                sale_order so
            WHERE
                so.invoice_status = 'to invoice'
                AND so.partner_id IS NOT NULL
            GROUP BY
                so.partner_id) S ON rp.id = S.partner_id
        LEFT JOIN (
            SELECT
                aml.partner_id AS partner_id,
                SUM(aml.balance) AS daml_balance
            FROM
                account_move_line aml
            JOIN account_move am ON aml.move_id = am.id
            JOIN payment_mode pm ON am.payment_mode_id = pm.id
            JOIN
                account_account aa ON aa.id = aml.account_id
            WHERE
                aa.account_type  IN ('liability_payable', 'asset_receivable')
                AND aml.parent_state = 'draft'
                AND aml.partner_id IS NOT NULL
                AND am.line_count > 0.0
                AND pm.is_credit_payment = true
            GROUP BY
                aml.partner_id) DAML
         ON rp.id = DAML.partner_id'''

    @api.model
    def _where(self):
        return '''WHERE 
        rp.customer_rank > 0
        AND rp.active = TRUE
        AND rp.customer_type = 'b2b'
        AND pst.is_delivery_service = TRUE'''

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
        CREATE OR REPLACE VIEW customer_balance AS (
                        %s
                        %s
                        %s)
                        """ % (self._select(), self._from(), self._where())
        self.env.cr.execute(query)
