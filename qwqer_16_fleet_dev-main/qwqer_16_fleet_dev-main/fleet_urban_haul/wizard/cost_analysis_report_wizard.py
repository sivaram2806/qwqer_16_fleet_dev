from odoo import fields, models
from odoo.exceptions import ValidationError


class CostAnalysisReportWizard(models.TransientModel):
    _name = "cost.analysis.report.wizard"
    _description = "Wizard to filter and generate cost analysis report"

    from_date = fields.Date(string='Date From')
    to_date = fields.Date(string='Date To')
    vendor_id = fields.Many2one('res.partner', string='Vendor', domain= lambda self:  [("company_id", "=", self.env.company.id)])
    customer_id = fields.Many2one('res.partner', string='Customer', domain= lambda self:  [("company_id", "=", self.env.company.id)])
    region_id = fields.Many2one('sales.region', string='Region', domain= lambda self:  [("company_id", "=", self.env.company.id)])
    vehicle_model_id = fields.Many2one('fleet.vehicle.model')
    sales_person_id = fields.Many2one('hr.employee')
    vehicle_pricing_id = fields.Many2one('vehicle.pricing', string='Vehicle Pricing')

    def action_cost_analysis(self):
        """Method to generate xlsx report with filtered data
        """
        for rec in self:
            if rec.from_date > rec.to_date:
                raise ValidationError('From Date must be less than To Date!!!')
            report = self.sudo().env.ref('fleet_urban_haul.cost_analysis_report_xlsx')
            report.report_file = "Cost_Analysis_Report"
            data = {
                'ids': self.env.context.get('active_ids', []),
                'model': 'cost.analysis.report.wizard',
            }
            return report.report_action(self, data=data)
