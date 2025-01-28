# -*- coding: utf-8 -*-

from odoo import api, fields, models
import time

class AccountingReport(models.TransientModel):
    _inherit = 'accounting.report'
    
    report_format = fields.Selection([('pdf', 'PDF'), ('excel', 'Excel')], string="Report Format", default="excel")
    used_context = fields.Char()
    trail_bal = fields.Boolean('Trial Balance')
    show_zero_bal = fields.Boolean(string="Show Zero Balance", default=False)
    filter_cmp = fields.Selection([('filter_no', 'No Filters'), ('filter_date', 'Date')], string='Filter by', required=True, default='filter_no')
    display_analytic_acc = fields.Boolean('Display Analytic Account')
    state_ids = fields.Many2many('res.country.state',string="State",
                                 domain=lambda self: [('country_id', '=', self.env.company.country_id.id)])
    region_ids = fields.Many2many('sales.region', string="Region")
    group_by_condition = fields.Selection([('region', 'Region'), ('state', 'State')], string='Group By',default="region")
    is_cash_flow = fields.Boolean("Is CashFlow Report",default=False)
    service_type_id = fields.Many2one(comodel_name='partner.service.type', string='Service Type')
    access_view = fields.Boolean(string='type visibility', default=False)
    include_opening = fields.Boolean('Show Opening Balance?', default=True)
    
    @api.onchange('state_ids')
    def onchange_state(self):
        state_ids = self.state_ids.ids
        for wiz in self:
            if not wiz.state_ids:
                state_ids = self.env['res.country.state'].search([]).ids
            return {'domain': {'region_ids': [('state_id','in',state_ids)]}}
        
    @api.onchange('region_ids')
    def onchange_region(self):
        region_ids = self.region_ids.ids
        for wiz in self:
            if not wiz.region_ids:
                region_ids = self.env['sales.region'].search([]).ids
            return {'domain': {'state_ids': [('regions_ids','in',region_ids)]}}
    
    @api.onchange('account_report_id')
    def onchange_account_report_id(self):
        if self.account_report_id and self.account_report_id.trial_balance:
            self.trail_bal = True
            self.debit_credit = True
            self.enable_filter = False
            self.display_analytic_acc = False
            self.date_from = time.strftime("%Y-01-01")
            self.date_to = time.strftime("%Y-%m-%d")
            self.is_cash_flow = False
        else:
            self.trail_bal = False
            self.date_from = time.strftime("%Y-01-01")
            self.date_to = time.strftime("%Y-%m-%d")
            self.is_cash_flow = False
            
        cashflow_stmt_id = self.env.ref('base_accounting_kit.account_financial_report_cash_flow0').id
        if self.account_report_id.id == cashflow_stmt_id:
            self.is_cash_flow = True
            self.debit_credit = False
            self.enable_filter = False
            self.display_analytic_acc = False
            self.include_opening = False
        else:
            self.is_cash_flow = False
        profit_loss_id = self.env.ref('base_accounting_kit.account_financial_report_profitandloss0').id
        if self.account_report_id.id == profit_loss_id:
            self.access_view=True
            self.debit_credit = False
            self.include_opening = True
        else:
            self.access_view=False
            
        
        
            
    @api.onchange('enable_filter')
    def onchange_enable_filter(self):
        if self.enable_filter:
            self.display_analytic_acc = False
            
    @api.onchange('trail_bal')
    def onchange_trail_bal(self):
        if self.trail_bal:
            self.display_analytic_acc = False
            self.debit_credit = True
            self.include_opening = True
            self.enable_filter = False


    
    @api.model
    def default_get(self, fields_list):
        res = super(AccountingReport, self).default_get(fields_list)
        pl_report = self.env.context.get('is_pl_report', False)
        if pl_report:
            res.update({
                'include_opening' : False,
                'debit_credit' : True
            })
        return res
    
    
    # @api.multi
    def _print_report(self, data):
        data = {}
        data['form'] = self.read()[0]
        for field in ['account_report_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        comparison_context = self._build_comparison_context(data)
        data['form']['comparison_context'] = comparison_context
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        data1= data
        report_format = data['form']['report_format']
        report_type = self._context.get('report_type',False)
        if not report_type:
            report_type = report_format
        if report_type == 'pdf':
            data1['form'].update(self.read(['account_report_id'])[0])
            res = self.env.ref('accounting_pdf_reports.action_report_financial').report_action(self, data=data1, config=False)
        elif report_type == 'html':
            data1['form'].update(self.read(['account_report_id'])[0])
            res = self.env.ref('account_financial_pl_bs.action_report_financial_html').report_action(self, data=data1, config=False)
        else:
            file_name = self.env.ref('account_financial_pl_bs.balance_sheet_xlsx1').report_file
            cashflow_stmt_id = self.env.ref('base_accounting_kit.account_financial_report_cash_flow0').id
            profit_loss_id = self.env.ref('base_accounting_kit.account_financial_report_profitandloss0').id
            balance_sheet_stmt_id = self.env.ref('base_accounting_kit.account_financial_report_balancesheet0').id
            balance_sheet_details_id = self.env.ref('base_accounting_kit.account_financial_report_balancesheet_details0').id
            
            if self.account_report_id.id == balance_sheet_details_id:
                file_name = "Balance_sheet_details" 
            if self.account_report_id.id == cashflow_stmt_id:
                file_name = "Cash_Flow_Statement"
            if self.account_report_id.id == profit_loss_id:
                file_name = "Profit_Loss"
                if self.service_type_id.is_qshop_service:
                    file_name = "QShop Profit_Loss"
                if self.service_type_id.is_delivery_service:
                    file_name = "Delivery Profit_Loss"
                if self.service_type_id.is_fleet_service:
                    file_name = "Fleet Profit_Loss"
            if self.account_report_id.id == balance_sheet_stmt_id:
                file_name = "Balance_sheet"
            self.env.ref('account_financial_pl_bs.balance_sheet_xlsx1').report_file = file_name
            self.env.ref('account_financial_pl_bs.balance_sheet_xlsx1').name = file_name
            res =  self.env.ref('account_financial_pl_bs.balance_sheet_xlsx1').with_context(rep_data=data).report_action(self, data=data1, config=False)
        return res
