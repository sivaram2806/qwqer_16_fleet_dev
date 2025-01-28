# -*- coding: utf-8 -*-
from odoo import fields, models


class FtlCostAnalysisReportWizard(models.TransientModel):
    _name = "ftl.cost.analysis.report.wizard"
    _description = "Wizard for FTL cost analysis report with customer, vendor and work order filter"

    customer_id = fields.Many2one('res.partner', string='Customer', domain= lambda self:  [("company_id", "=", self.env.company.id)])
    vendor_id = fields.Many2one('res.partner', string='Vendor', domain= lambda self:  [("company_id", "=", self.env.company.id)])
    work_order_id = fields.Many2one('work.order', string='Work Order', domain= lambda self:  [("company_id", "=", self.env.company.id)])
    sales_person_id = fields.Many2one('res.partner', string="Sales Person", domain= lambda self:  [("company_id", "=", self.env.company.id)])

    def action_ftl_cost_analysis(self):
        """Method to call report action with data to generate"""
        report = self.env.ref('fleet_ftl.ftl_cost_analysis_report_xlsx')
        report.report_file = "Ftl_Cost_Analysis_Report"
        data = {
            'ids': self.env.context.get('active_ids', []),
            'model': 'ftl.cost.analysis.report.wizard',
        }
        return report.report_action(self, data=data)
