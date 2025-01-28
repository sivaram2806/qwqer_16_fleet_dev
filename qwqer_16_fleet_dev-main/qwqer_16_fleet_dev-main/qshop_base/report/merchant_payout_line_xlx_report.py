# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models
from odoo.exceptions import UserError
from pytz import timezone, UTC


class QwqerShopMerchantPayoutLinesReport(models.AbstractModel):
    _name = 'report.qshop_merchant_payout_lines_xlsx'
    _inherit = "report.report_xlsx.abstract"
    _description = 'Shop Merchant Payout Lines Report'

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
            'header': workbook.add_format({'align': 'center', 'font_size': 12, 'bold': True}),
            'sub_header': workbook.add_format({'align': 'center', 'font_size': 10, 'bold': True}),
            'highlight_header': workbook.add_format(
                {'align': 'center', 'font_size': 10, 'bold': True, 'bg_color': '#808080'}),
            'date_header': workbook.add_format(
                {'num_format': 'dd-mmm-yy', 'font_size': 10, 'align': 'center', 'bold': True}),
            'date': workbook.add_format({'num_format': 'dd-mmm-yy', 'font_size': 10, 'align': 'left'}),
            'border': workbook.add_format({'border': 3, 'border_color': 'red'}),
        }

        # WORKSHEET CONFIGURATION
        worksheet = workbook.add_worksheet('Payout Details')
        worksheet.set_column('A:A', 18)
        worksheet.set_column('B:B', 40)
        worksheet.set_column('C:C', 16)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)

        # TITLE
        worksheet.merge_range('A1:E2', "Merchant Amount Collection Report", formats['header'])

        # ROW INITIALIZATION
        row = 4
        column = 0

        # HELPER FUNCTION TO WRITE DATA
        def write_cell(row, col, label, value, text_format, fallback=""):
            worksheet.write(row, col, label, formats['cell_text'])
            worksheet.write(row, col + 1, value if value else fallback, text_format)

        # HEADER CONTENT
        content = [
            ('Transfer ID', active_model.transfer_ref, formats['text']),
            ('Customer', active_model.customer_id.name, formats['text']),
            ('Region', active_model.region_id.name, formats['text']),
            ('Payment Gateway Ref#', active_model.cashfree_ref, formats['text']),
            ('UTR', active_model.utr_ref, formats['text']),
            ('From Date', active_model.from_date, formats['date']),
            ('To Date', active_model.to_date, formats['date']),
            ('Transaction Date', active_model.transfer_date, formats['date']),
            ('Processed Date', active_model.processed_date, formats['date']),
        ]

        for label, value, text_format in content:
            write_cell(row, column, label, value, text_format)
            row += 1

        amounts = [
            ('Total Amount (A)', active_model.total_pay, formats['num']),
            ('TDS (B)', active_model.tds, formats['num']),
            ('TCS (C)', active_model.tcs, formats['num']),
            ('Deduction (D)', active_model.balance_amt, formats['num']),
            ('Service Charge (E)', active_model.service_charge, formats['num']),
            ('Taxes (F)', active_model.taxes, formats['num']),
            ('Total Payout (A-B-C-D-E-F)', active_model.final_pay, formats['num']),

        ]

        row = 5
        for label, value, fmt in amounts:
            worksheet.write(row, 3, label, formats['cell_text'])
            worksheet.write(row, 4, value or 0.00, fmt)
            row += 1

        # TRANSACTION TABLE
        row += 4
        worksheet.write(row, column, 'Transactions', formats['header'])

        row += 2
        transactions_data = []
        for line in active_model.line_ids:
            order_date = self.get_local_datetime(line.date_order)
            transactions_data.append([
                line.merchant_order_id.name or "",
                line.order_id or "",
                order_date or "",
                line.move_id.name or "",
                line.debit or 0.0,
                line.credit or 0.0,
            ])

        worksheet.add_table(
            row, column, row + len(transactions_data), column + 5,
            {
                'data': transactions_data,
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
