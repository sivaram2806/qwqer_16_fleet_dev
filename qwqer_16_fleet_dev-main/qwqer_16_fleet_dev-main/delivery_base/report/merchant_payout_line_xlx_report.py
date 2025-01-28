# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, _
from odoo.exceptions import UserError
from pytz import timezone, UTC

class MerchantPayoutLinesReport(models.AbstractModel):
    _name = 'report.delivery_merchant_payout_lines_xlsx'
    _inherit = "report.report_xlsx.abstract"
    _description = 'Merchant Payout Lines Report'

    def get_local_datetime(self, date):
        if not date:
            return None
        tz_name = self._context.get('tz') or self.env.user.tz
        if not tz_name:
            raise UserError(_('Please configure your time zone in Preferences'))
        try:
            user_tz = timezone(tz_name)
            local_time = UTC.localize(date).astimezone(user_tz)
            return local_time.strftime('%d-%m-%Y %H:%M:%S')
        except Exception as e:
            raise UserError(_('Error converting time: %s') % e)

    def generate_xlsx_report(self, workbook, data, active_model):
        # FORMATS
        formats = {
            'cell_text': workbook.add_format({'align': 'left', 'bold': True, 'font_size': 10}),
            'cell_num': workbook.add_format(
                {'align': 'right', 'bold': True, 'font_size': 10, 'num_format': '#,##0.00'}),
            'text': workbook.add_format({'align': 'left', 'bold': False, 'font_size': 10}),
            'num': workbook.add_format({'align': 'right', 'bold': False, 'font_size': 10, 'num_format': '#,##0.00'}),
            'header': workbook.add_format({'align': 'center', 'bold': True, 'font_size': 12}),
            'header2': workbook.add_format({'align': 'center', 'bold': True, 'font_size': 10}),
            'date_header': workbook.add_format(
                {'num_format': 'dd-mmm-yy', 'align': 'center', 'bold': True, 'font_size': 10}),
            'date': workbook.add_format({'num_format': 'dd-mmm-yy', 'align': 'left', 'font_size': 10}),
        }

        worksheet = workbook.add_worksheet('Payout Details')
        worksheet.set_column('A:A', 18)
        worksheet.set_column('B:B', 40)
        worksheet.set_column('C:C', 16)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)

        # HEADER
        worksheet.merge_range('A1:E2', "Merchant Amount Collection Report", formats['header'])

        # Helper to write row data
        def write_row(label, value, row, col=0, value_format=formats['text']):
            worksheet.write(row, col, label, formats['cell_text'])
            worksheet.write(row, col + 1, value or "", value_format)

        # WRITE DETAILS
        row = 4
        details = [
            ('Transfer ID', active_model.transfer_ref, formats['text']),
            ('Customer', active_model.customer_id and active_model.customer_id.name, formats['text']),
            ('Region', active_model.region_id and active_model.region_id.name, formats['text']),
            ('Payment Gateway Ref#', active_model.cashfree_ref, formats['text']),
            ('UTR', active_model.utr_ref, formats['text']),
            ('From Date', active_model.from_date, formats['date']),
            ('To Date', active_model.to_date, formats['date']),
            ('Transaction Date', active_model.transfer_date, formats['date']),
            ('Processed Date', active_model.processed_date, formats['date']),
        ]

        for label, value, fmt in details:
            write_row(label, value, row, value_format=fmt)
            row += 1

        # WRITE AMOUNTS
        amounts = [
            ('Total Amount (A)', active_model.total_pay, formats['num']),
            ('Deduction (B)', active_model.balance_amt, formats['num']),
            ('Service Charge (C)', active_model.service_charge, formats['num']),
            ('Taxes (D)', active_model.taxes, formats['num']),
            ('Total Payout (A-B-C-D)', active_model.final_pay, formats['num']),
        ]

        row = 5
        for label, value, fmt in amounts:
            worksheet.write(row, 3, label, formats['cell_text'])
            worksheet.write(row, 4, value or 0.00, fmt)
            row += 1

        # TRANSACTIONS TABLE
        row += 4
        worksheet.write(row, 0, 'Transactions', formats['header'])
        row += 2

        table_data = [
            [
                line.merchant_order_id.name or "",
                line.order_id or "",
                self.get_local_datetime(line.date_order) or "",
                line.move_id.name or "",
                line.debit or 0.00,
                line.credit or 0.00
            ]
            for line in active_model.line_ids
        ]

        worksheet.add_table(
            row, 0, row + len(table_data), 5,
            {
                'data': table_data,
                'columns': [
                    {'header': 'Merchant Sale Order'},
                    {'header': 'Order ID'},
                    {'header': 'Order Date'},
                    {'header': 'Journal Entry'},
                    {'header': 'Debit'},
                    {'header': 'Credit'},
                ],
            }
        )

        workbook.close()
