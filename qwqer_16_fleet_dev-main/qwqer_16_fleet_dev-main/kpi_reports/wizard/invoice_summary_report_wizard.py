from odoo import models, fields


class InvoiceSummaryReport(models.TransientModel):
    _name = 'invoice.summary.report.wizard'

    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date', required=True)
    partner_ids = fields.Many2many('res.partner', string='Partner')

    def print_invoice_summary_xl_report(self):
        return self.env.ref('kpi_reports.invoice_summary_xl_report').report_action(self, data=self.read([])[0])


