# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.tools.safe_eval import safe_eval

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    @api.model
    def _query_get(self, domain=None):
        context = dict(self._context or {})
        domain = domain and safe_eval(str(domain)) or []
        date_field = 'date'
        if context.get('aged_balance'):
            date_field = 'date_maturity'
        if context.get('date_to'):
            domain += [(date_field, '<=', context['date_to'])]
        if context.get('date_from'):
            if context.get('initial_bal'):
                domain += [(date_field, '<', context['date_from']),('account_id.include_initial_balance', '=', True)]
            else:
                domain += [(date_field, '>=', context['date_from'])]

        state = context.get('state')
        if state and state.lower() != 'all':
            domain += [('move_id.state', '=', state)]

        if context.get('company_id'):
            domain += [('company_id', '=', context['company_id'])]

        if 'company_ids' in context:
            domain += [('company_id', 'in', context['company_ids'])]

        if context.get('reconcile_date'):
            domain += ['|', ('reconciled', '=', False), '|', ('matched_debit_ids.create_date', '>', context['reconcile_date']), ('matched_credit_ids.create_date', '>', context['reconcile_date'])]
        where_clause = ""
        where_clause_params = []
        tables = ''
        if domain:
            query = self._where_calc(domain)
            tables, where_clause, where_clause_params = query.get_sql()
        return tables, where_clause, where_clause_params
