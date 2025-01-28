from odoo import models, fields
import logging
import datetime
from datetime import datetime
import pytz
import json
_logger = logging.getLogger('__name__')


class SalespersonSummaryReport(models.AbstractModel):
    _name = "report.kpi_reports.salesperson_summary_report_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, obj):
        cell_text_format = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 10})
        format3 = workbook.add_format({'align': 'left', 'bold': False, 'font_size': 10})
        head = workbook.add_format({'align': 'center', 'size': 12, 'bold': True})
        head2 = workbook.add_format({'align': 'center', 'size': 10, 'bold': True})
        worksheet = workbook.add_worksheet('Salesperson.xlsx')
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
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 16)
        worksheet.set_column('C:C', 12)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 33)
        worksheet.set_column('G:G', 33)

        worksheet.merge_range('A1:F2', company_name, head)
        worksheet.merge_range('A3:F4', company_addr, head2)
        worksheet.merge_range('A5:F6', company_addr1, head2)

        row = 7
        column = 0

        worksheet.merge_range('B7:E7', 'Sales Person Summary Report', head)
        row += 2

        from_date = fields.Date.from_string(data['from_date']).strftime('%d/%m/%Y')
        to_date = fields.Date.from_string(data['to_date']).strftime('%d/%m/%Y')

        worksheet.write(row, column, 'From Date', cell_text_format)
        worksheet.write(row, column + 1, from_date, cell_text_format)
        worksheet.write(row, column + 3, 'To Date', cell_text_format)
        worksheet.write(row, column + 4, to_date, cell_text_format)

        row += 2
        worksheet.write(row, column , 'Sales Person Name', cell_text_format)
        worksheet.write(row, column + 1, 'Sales Team', cell_text_format)
        worksheet.write(row, column + 2, 'Region', cell_text_format)
        worksheet.write(row, column + 3, 'Total Order per sales person', cell_text_format)
        worksheet.write(row, column + 4, 'Value per sales person', cell_text_format)
        worksheet.write(row, column + 5, 'Total customers under a sales person', cell_text_format)
        order_list = []
        domain = []
        local = pytz.timezone(self.env.user.tz or pytz.utc)

        from_date = data['from_date'] + ' ' + '00:00:00'
        _logger.info("From date %s", from_date)
        from_naive_schedule = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S")
        from_local_dt_schedule = local.localize(from_naive_schedule, is_dst=None)
        utc_from_date = from_local_dt_schedule.astimezone(pytz.utc)
        _logger.info("UTC From date %s", utc_from_date)

        to_date = data['to_date'] + ' ' + '23:59:59'
        _logger.info("To date %s", to_date)
        to_naive_schedule = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S")
        to_local_dt_schedule = local.localize(to_naive_schedule, is_dst=None)
        utc_to_date = to_local_dt_schedule.astimezone(pytz.utc)
        _logger.info("UTC To date %s", utc_to_date)

        if data['from_date']:
            domain.append(('date_order', '>=', utc_from_date))
        if data['to_date']:
            domain.append(('date_order', '<=', utc_to_date))
        if data['sales_person']:
            domain.append(('order_sales_person', '=', data['sales_person']))
        domain.append(('state', '=', 'sale'))
        sale_orders = self.env['sale.order'].search(domain)
        for order in sale_orders:
            if order.order_sales_person:
                if not any(ls['user_id'] == order.order_sales_person.id for ls in order_list):
                    order_count = self.env['sale.order'].search_count([('order_sales_person', '=', order.order_sales_person.id),
                                                                       ('date_order', '>=', utc_from_date),
                                                                       ('date_order', '<=', utc_to_date),
                                                                           ('state', '=', 'sale'),
                                                                           ])
                    customer_count = self.env['res.partner'].search_count([('order_sales_person', '=', order.order_sales_person.id)])
                    order_dic = {
                        "user_id": order.order_sales_person.id if order.order_sales_person else '',
                        "salesperson": order.order_sales_person.name if order.order_sales_person else '',
                        "salesteam": order.team_id.name,
                        "region": order.region_id.name if order.region_id else '',
                        "order_count": order_count,
                        "amount": order.amount_total,
                        "customer_count": customer_count
                    }
                    order_list.append(order_dic)
                else:
                    for i in order_list:
                        if i['user_id'] == order.user_id.id:
                            i.update({
                                'amount': i['amount'] + order.amount_total,
                            })
        order_list = sorted(order_list, key=lambda x: x['region'])
        for res in order_list:
            row += 1
            worksheet.write(row + 1, column , res['salesperson'], format3)
            worksheet.write(row + 1, column + 1, res['salesteam'], format3)
            worksheet.write(row + 1, column + 2, res['region'], format3)
            worksheet.write(row + 1, column + 3, res['order_count'], format3)
            worksheet.write(row + 1, column + 4, res['amount'], format3)
            worksheet.write(row + 1, column + 5, res['customer_count'], format3)