# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import time
from odoo import api, models, fields, _
from odoo.tools.misc import get_lang
from odoo.exceptions import UserError


class CashFlow(models.Model):
    _inherit = 'account.account'

    def get_financial_report_ids(self, report_xml_id):
        """
        Retrieve financial report IDs based on the hierarchy starting from the given report XML ID.
        """
        report_id = self.env.ref(report_xml_id).id
        parent_ids = [report_id]
        condition = True
        child_ids = self.env['account.financial.report'].search([('parent_id', '=', report_id)])

        while condition and child_ids:
            next_level_ids = []
            for report in child_ids:
                parent_ids.append(report.id)
                next_level_ids.append(report.id)
            child_ids = self.env['account.financial.report'].search([('parent_id', 'in', next_level_ids)])
            if not child_ids:
                condition = False

        return [('parent_id', 'in', parent_ids), ('type', '=', 'accounts')]

    def get_cash_flow_ids(self):
        """Get Cash Flow IDs."""
        return self.get_financial_report_ids('base_accounting_kit.account_financial_report_cash_flow0')

    def get_profit_loss_ids(self):
        """Get Profit & Loss IDs."""
        return self.get_financial_report_ids('base_accounting_kit.account_financial_report_profitandloss0')

    def get_balance_sheet_ids(self):
        """Get Balance Sheet IDs."""
        return self.get_financial_report_ids('base_accounting_kit.account_financial_report_balancesheet0')

    def get_balance_sheet_detailed_ids(self):
        """Get Balance Sheet Detailed IDs."""
        return self.get_financial_report_ids('base_accounting_kit.account_financial_report_balancesheet_details0')

    cash_flow_type = fields.Many2one('account.financial.report', string="Cash Flow type", domain=get_cash_flow_ids)
    is_pl_account = fields.Boolean(string="Is P&L Account")
    is_bs_account = fields.Boolean(string="Is Balance Sheet Account")
    profit_loss_hierarchy_id = fields.Many2one(
        'account.financial.report', string="Profit & Loss Hierarchy", domain=lambda self: self.get_profit_loss_ids()
    )
    balance_sheet_hierarchy_id = fields.Many2one(
        'account.financial.report', string="Balance Sheet Hierarchy", domain=lambda self: self.get_balance_sheet_ids()
    )
    bs_detailed_hierarchy_id = fields.Many2one(
        'account.financial.report', string="Balance Sheet Details Hierarchy",
        domain=lambda self: self.get_balance_sheet_detailed_ids()
    )

    @api.onchange('cash_flow_type')
    def onchange_cash_flow_type(self):
        if self._origin:
            # Remove old links
            for rec in self._origin.cash_flow_type:
                rec.write({'account_ids': [(3, self._origin.id)]})

            # Add new links
            for rec in self.cash_flow_type:
                rec.write({'account_ids': [(4, self._origin.id)]})

    @api.onchange('account_type')
    def onchange_account_type(self):
        if self.account_type:
            account_type = self.env['account.account.type'].search([('type', '=', self.account_type)], limit=1)
            self.is_pl_account = account_type.is_pl_account
            self.is_bs_account = not account_type.is_pl_account

    @api.model
    def create(self, vals):
        res = super().create(vals)
        self._update_hierarchy_links(res)
        return res

    def write(self, vals):
        self._clear_hierarchy_links()
        res = super().write(vals)
        self._update_hierarchy_links(self)
        return res

    def _update_hierarchy_links(self, records):
        """Update hierarchy links for the given records."""
        hierarchy_fields = {
            'profit_loss_hierarchy_id': 'account_ids',
            'balance_sheet_hierarchy_id': 'account_ids',
            'bs_detailed_hierarchy_id': 'account_ids',
        }
        for record in records:
            for field, link_field in hierarchy_fields.items():
                if getattr(record, field):
                    getattr(record, field).write({link_field: [(4, record.id)]})

    def _clear_hierarchy_links(self):
        """Clear hierarchy links before updating."""
        hierarchy_fields = [
            'profit_loss_hierarchy_id',
            'balance_sheet_hierarchy_id',
            'bs_detailed_hierarchy_id',
        ]
        for field in hierarchy_fields:
            if getattr(self, field):
                getattr(self, field).write({'account_ids': [(3, self.id)]})

    def update_hierarchy(self, report_type):
        """Generic method to update account hierarchy."""
        account_list = self.env['account.account'].search([])
        hierarchy_id = self.env.ref(f'base_accounting_kit.account_financial_report_{report_type}0').id
        self._process_hierarchy(hierarchy_id, account_list, report_type)

    def _process_hierarchy(self, hierarchy_id, account_list, report_type):
        """Recursively process hierarchy for the given type."""
        child_ids = self.env['account.financial.report'].search([('parent_id', '=', hierarchy_id)])
        while child_ids:
            next_level_ids = []
            for report in child_ids:
                if report.account_ids:
                    for acc in report.account_ids:
                        setattr(acc, f'is_{report_type}_account', True)
                        setattr(acc, f'{report_type}_hierarchy_id', report.id)
                next_level_ids.append(report.id)
            child_ids = self.env['account.financial.report'].search([('parent_id', 'in', next_level_ids)])

    def update_pl_hierarchy(self):
        self.update_hierarchy('profitandloss')

    def update_bs_hierarchy(self):
        self.update_hierarchy('balancesheet')
        self.update_hierarchy('balancesheet_details')



class AccountCommonReport(models.Model):
    _inherit = "account.report"
    _description = "Account Common Report"

    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string='Journals',
        required=True,
        default=lambda self: self.env['account.journal'].search([('company_id', '=', self.company_id.id)]),
        domain="[('company_id', '=', company_id)]",
    )
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.journal_ids = self.env['account.journal'].search(
                [('company_id', '=', self.company_id.id)])
        else:
            self.journal_ids = self.env['account.journal'].search([])

    def _build_contexts(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        result['company_id'] = data['form']['company_id'][0] or False
        return result

    def _print_report(self, data):
        raise NotImplementedError()

    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        return self.with_context(discard_logo_check=True)._print_report(data)


class AccountCommonJournalReport(models.TransientModel):
    _name = 'account.common.journal.report'
    _description = 'Common Journal Report'
    _inherit = "account.report"

    amount_currency = fields.Boolean('With Currency', help="Print Report with the currency column if the currency differs from the company currency.")

    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')

    def pre_print_report(self, data):
        data['form'].update({'amount_currency': self.amount_currency})
        return data

    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        return self.with_context(discard_logo_check=True)._print_report(data)

    def _build_contexts(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        result['company_id'] = data['form']['company_id'][0] or False
        return result




