from odoo import models, fields
import logging

_logger = logging.getLogger('__name__')


class InvoiceExcelReport(models.AbstractModel):
    _name = "report.kpi_reports.invoice_summary_xl_report"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, obj):
        cell_text_format = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 10})
        format3 = workbook.add_format({'align': 'left', 'bold': False, 'font_size': 10})
        head = workbook.add_format({'align': 'center', 'size': 12, 'bold': True})
        head2 = workbook.add_format({'align': 'center', 'size': 10, 'bold': True})
        head3 = workbook.add_format({'align': 'center', 'font_size': 10, 'bold': True, 'bg_color': '#808080'})
        worksheet = workbook.add_worksheet('Invoice.xlsx')
        company_name = self.env.user.company_id.name
        company_street = self.env.user.company_id.street if self.env.user.company_id.street else ''
        company_street2 = self.env.user.company_id.street2 if self.env.user.company_id.street2 else ''
        company_city = self.env.user.company_id.city if self.env.user.company_id.city else ''
        company_zip = self.env.user.company_id.zip if self.env.user.company_id.zip else ''
        company_addr = str(company_street + ' , ' + ' ' + company_street2 + '  ' + company_city + '  ' + company_zip)
        company_mob = self.env.user.company_id.phone if self.env.user.company_id.phone else ''
        company_email = self.env.user.company_id.email if self.env.user.company_id.email else ''
        company_website = self.env.user.company_id.website if self.env.user.company_id.website else ''
        if company_mob and company_email and company_website:
            company_addr1 = 'Ph:' + company_mob + ',' + ' ' + 'Email:' + company_email + ',' + ' ' + 'Website:' + company_website
        else:
            company_addr1 = ''
        worksheet.set_column('A:A', 22)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 35)
        worksheet.set_column('F:F', 35)

        worksheet.merge_range('A1:F2', company_name, head)
        worksheet.merge_range('A3:F4', company_addr, head2)
        worksheet.merge_range('A5:F6', company_addr1, head2)

        row = 7
        column = 0

        worksheet.merge_range('B7:E7', 'Invoice Summary Report', head)
        row += 2

        from_date = fields.Date.from_string(data['from_date']).strftime('%d/%m/%Y')
        to_date = fields.Date.from_string(data['to_date']).strftime('%d/%m/%Y')

        worksheet.write(row, column, 'From Date', cell_text_format)
        worksheet.write(row, column + 1, from_date, cell_text_format)
        worksheet.write(row, column + 3, 'To Date', cell_text_format)
        worksheet.write(row, column + 4, to_date, cell_text_format)

        row += 2
        worksheet.write(row, column, 'Customer Name', cell_text_format)
        worksheet.write(row, column + 1, 'Region', cell_text_format)
        worksheet.write(row, column + 2, 'No of Invoices generated', cell_text_format)
        worksheet.write(row, column + 3, 'Value of Invoice generated', cell_text_format)
        worksheet.write(row, column + 4, 'Outstanding Payment for customer(Qty/No)', cell_text_format)
        worksheet.write(row, column + 5, 'Outstanding Payment for customer(Value)', cell_text_format)

        self.env.cr.execute("""select
                res_partner.name as CUSTOMER, sales_region.name as REGION, count(account_move) as NO_OF_INVOICES,

                sum(account_move.amount_total) as TOTAL_VALUE,

                SUM(CASE
                WHEN(account_move.amount_residual > 0)
                THEN 1 ELSE 0 END) as BALANCE_COUNT,

                sum(account_move.amount_residual) as TOTAL_BALANCE

                from res_partner, sales_region, account_move

                where res_partner.region_id = sales_region.id and account_move.partner_id = res_partner.id and 
                account_move.invoice_date >= %s and account_move.invoice_date <= %s
                group by res_partner.name, sales_region.name order by sales_region.name""", (data['from_date'], data['to_date']))

        data = self.env.cr.fetchall()
        for item in data:
            row += 1
            worksheet.write(row + 1, column, item[0], format3)
            worksheet.write(row + 1, column + 1, item[1], format3)
            worksheet.write(row + 1, column + 2, item[2], format3)
            worksheet.write(row + 1, column + 3, item[3], format3)
            worksheet.write(row + 1, column + 4, item[4], format3)
            worksheet.write(row + 1, column + 5, item[5], format3)