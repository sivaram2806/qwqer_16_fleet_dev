from odoo import models, fields


class SalespersonSummaryReport(models.TransientModel):
    _name = 'sales.person.summary.report.wizard'

    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date', required=True)
    sales_person = fields.Many2many('hr.employee', string='Salesperson')

    def print_salesperson_summary_report_xl(self):
        return self.env.ref('kpi_reports.salesperson_summary_report_xl').report_action(self, data=self.read([])[0])


