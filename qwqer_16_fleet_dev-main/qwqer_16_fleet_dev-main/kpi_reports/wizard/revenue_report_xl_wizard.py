from odoo import models, fields


class RevenueReportWizard(models.TransientModel):
    _name = 'revenue.report.wizard'

    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date', required=True)
    partner_ids = fields.Many2many('res.partner', string='Partner')

    def print_revenue_xl_report(self):
        return self.env.ref('kpi_reports.revenue_report_xl').report_action(self, data=self.read([])[0])
