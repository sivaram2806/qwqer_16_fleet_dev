# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api


class PartnerBalance(models.Model):
    _name = "partner.balance"
    _description = "Partner Balance"
    _auto = False
    _rec_name = 'customer_id'

    customer_id = fields.Many2one(comodel_name='res.partner', string='Customer ID')
    customer = fields.Char(string='Customer Name')
    customer_rank = fields.Integer(default=0)
    region_id = fields.Many2one(comodel_name='sales.region', string='Region')
    service_type_id = fields.Many2one(comodel_name='partner.service.type', string='Service Type')
    segment_id = fields.Many2one(comodel_name='partner.segment', string='Segment')
    order_sales_person = fields.Many2one(comodel_name='hr.employee', string='Sales Person')
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    credit = fields.Float(string="Invoice Receivable")
    debit = fields.Float(string="Invoice Payable")
    due_amount = fields.Float(string="Balance")

    @api.model
    def _sum_due_amount(self):
        return ''',
        COALESCE(R.credit,0) + COALESCE(P.debit,0) '''

    @api.model
    def _select(self):
        return '''SELECT 
        rp.id,
        rp.id as customer_id,
        rp.display_name AS customer,
        rp.customer_rank,
        rp.region_id,
        rp.service_type_id,
        rp.segment_id,
        rp.order_sales_person,
        rp.company_id,
        R.credit,
        P.debit''' + '''%s''' % self._sum_due_amount() + ''' as due_amount'''

    @api.model
    def _from(self):
        return '''FROM
        res_partner rp
        LEFT JOIN (
            SELECT
                aml.partner_id as partner_id,
                COALESCE(sum(aml.balance), 0.00) AS credit
            FROM account_move_line aml
                LEFT JOIN
                    (SELECT id, account_type
                     FROM account_account 
                    ) account ON aml.account_id = account.id
            WHERE
                account.account_type='asset_receivable' and aml.parent_state='posted' and aml.partner_id IS NOT NULL
            GROUP BY
                aml.partner_id
            ORDER BY
                aml.partner_id) R on rp.id=R.partner_id
        LEFT JOIN (
            SELECT
                aml.partner_id as partner_id,
                COALESCE(sum(aml.balance), 0.00) as debit
            FROM account_move_line aml
                LEFT JOIN
                    (SELECT id, account_type
                     FROM account_account
                    ) account ON aml.account_id = account.id
            WHERE
                account.account_type='liability_payable' and aml.parent_state='posted' and aml.partner_id IS NOT NULL
            GROUP BY
                aml.partner_id
            ORDER BY
                aml.partner_id) P on rp.id=P.partner_id'''

    @api.model
    def _where(self):
        return '''WHERE rp.customer_rank > 0'''

    @api.model
    def _group_by(self):
        return '''GROUP BY 
        R.credit,
        P.debit,
        rp.id'''

    @api.model
    def _order_by(self):
        return '''ORDER BY
        rp.id'''

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        query = """
        CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
                %s)
        """ % (self._table, self._select(), self._from(), self._where(), self._group_by(), self._order_by())
        self._cr.execute(query)
