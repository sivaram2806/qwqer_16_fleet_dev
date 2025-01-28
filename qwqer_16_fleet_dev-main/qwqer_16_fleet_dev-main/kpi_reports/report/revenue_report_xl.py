from odoo import models, fields
import logging
import datetime
from datetime import datetime
import pytz
import json

_logger = logging.getLogger('__name__')

class RevenueExcelReport(models.AbstractModel):
    """
    This model generates an Excel report for revenue data.
    """
    _name = "report.kpi_reports.revenue_report_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, obj):
        """
        Generates the Excel report for revenue data.

        :param workbook: The workbook object where the report will be generated.
        :param data: The data dictionary containing the report parameters.
        :param obj: The object for which the report is generated.
        """
        cell_text_format = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 10})
        format3 = workbook.add_format({'align': 'left', 'bold': False, 'font_size': 10})
        head = workbook.add_format({'align': 'center', 'font_size': 12, 'bold': True})
        head2 = workbook.add_format({'align': 'center', 'font_size': 10, 'bold': True})
        head3 = workbook.add_format({'align': 'center', 'font_size': 10, 'bold': True, 'bg_color': '#808080'})
        worksheet = workbook.add_worksheet('Revenue.xlsx')

        # Company details
        company = self.env.user.company_id
        company_name = company.name
        company_addr = f"{company.street or ''}, {company.street2 or ''}, {company.city or ''}, {company.zip or ''}"
        company_contact = f"Ph: {company.phone or ''}, Email: {company.email or ''}, Website: {company.website or ''}"

        worksheet.set_column('A:H', 22)
        worksheet.merge_range('A1:H1', company_name, head)
        worksheet.merge_range('A2:H2', company_addr, head2)
        worksheet.merge_range('A3:H3', company_contact, head2)

        row = 4
        worksheet.merge_range('B5:E5', 'Revenue Report', head)
        row += 2

        # Date range for the report
        from_date = fields.Date.from_string(data['from_date']).strftime('%d/%m/%Y')
        to_date = fields.Date.from_string(data['to_date']).strftime('%d/%m/%Y')

        worksheet.write(row, 0, 'From Date', cell_text_format)
        worksheet.write(row, 1, from_date, cell_text_format)
        worksheet.write(row, 3, 'To Date', cell_text_format)
        worksheet.write(row, 4, to_date, cell_text_format)

        row += 2
        headers = ['Sl. No', 'Customer Name', 'Region', 'No of Order per customer', 'Value of orders placed by customer', 'Taxable value of orders', 'SGST', 'CGST']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, cell_text_format)

        # Convert dates to UTC
        from_date_utc = fields.Datetime.to_datetime(data['from_date'] + ' 00:00:00').astimezone(pytz.utc)
        to_date_utc = fields.Datetime.to_datetime(data['to_date'] + ' 23:59:59').astimezone(pytz.utc)

        # Search for posted invoices within the date range
        domain = [
            ('invoice_date', '>=', data['from_date']),
            ('invoice_date', '<=', data['to_date']),
            ('state', '=', 'posted')
        ]
        if data.get('partner_ids'):
            domain.append(('partner_id', 'in', data['partner_ids']))

        invoices = self.env['account.move'].search(domain)
        partner_orders = {}

        # Aggregate invoice data by partner
        for inv in invoices:
            partner_id = inv.partner_id.id
            if partner_id not in partner_orders:
                partner_orders[partner_id] = {
                    "customer": inv.partner_id.name or '',
                    "region": inv.partner_id.region_id.name or '',
                    "order_count": 0,
                    "amount": 0.0,
                    "taxable_value": 0.0,
                    "sgst": 0.0,
                    "cgst": 0.0,
                }
            partner_orders[partner_id]['taxable_value'] += inv.amount_untaxed
            partner_orders[partner_id]['sgst'] += sum(line.price_total - line.price_subtotal for line in inv.invoice_line_ids if 'SGST' in line.tax_ids.mapped('name'))
            partner_orders[partner_id]['cgst'] += sum(line.price_total - line.price_subtotal for line in inv.invoice_line_ids if 'CGST' in line.tax_ids.mapped('name'))

        # Search for sale orders within the date range for each partner
        for partner_id, values in partner_orders.items():
            orders = self.env['sale.order'].search([
                ('partner_id', '=', partner_id),
                ('date_order', '>=', from_date_utc),
                ('date_order', '<=', to_date_utc),
                ('state', '=', 'sale')
            ])
            values['order_count'] = len(orders)
            values['amount'] = sum(order.amount_total for order in orders)

        # Write aggregated data to the worksheet
        for index, (partner_id, values) in enumerate(partner_orders.items(), start=1):
            row += 1
            worksheet.write(row, 0, index, format3)
            worksheet.write(row, 1, values['customer'], format3)
            worksheet.write(row, 2, values['region'], format3)
            worksheet.write(row, 3, values['order_count'], format3)
            worksheet.write(row, 4, values['amount'], format3)
            worksheet.write(row, 5, '%.2f' % values['taxable_value'], format3)
            worksheet.write(row, 6, values['sgst'], format3)
            worksheet.write(row, 7, values['cgst'], format3)
