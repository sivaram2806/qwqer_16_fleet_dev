from operator import itemgetter
from datetime import datetime
import json
from datetime import datetime

from odoo import fields, models, api, _


class WeeklyMonthlyXlsx(models.AbstractModel):
    _name = 'report.driver_management.report_weekly_monthly_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, active_model):
        # FORMATS STARTS
        design_formats = {'heading_format': workbook.add_format({'align': 'center',
                                                                 'valign': 'vcenter',
                                                                 'bold': True, 'size': 11,
                                                                 'font_name': 'Times New Roman',
                                                                 'text_wrap': True,
                                                                 # 'bg_color': 'blue', 'color' : 'white',
                                                                 'text_wrap': True, 'shrink': True}),
                          'heading_format_1': workbook.add_format({'align': 'left',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   'bg_color': 'FFFFCC', 'color': 'black',
                                                                   'border': True,
                                                                   'text_wrap': True, 'shrink': True}),
                          'heading_format_2': workbook.add_format({'align': 'center',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   'bg_color': 'FFFFCC', 'color': 'black',
                                                                   'border': True,
                                                                   'text_wrap': True, 'shrink': True}),
                          'merged_format': workbook.add_format({'align': 'center',
                                                                'valign': 'vjustify',
                                                                'bold': True, 'size': 17,
                                                                'font_name': 'Times New Roman',
                                                                # 'bg_color': 'blue', 'color' : 'white',
                                                                'text_wrap': True, 'shrink': True}),
                          'sub_heading_format': workbook.add_format({'align': 'right',
                                                                     'valign': 'vjustify',
                                                                     'bold': True, 'size': 9,
                                                                     'font_name': 'Times New Roman',
                                                                     # 'bg_color': 'yellow', 'color' : 'black',
                                                                     'text_wrap': True, 'shrink': True}),
                          'sub_heading_format_left': workbook.add_format({'align': 'left',
                                                                          'valign': 'vjustify',
                                                                          'bold': False, 'size': 9,
                                                                          'font_name': 'Times New Roman',
                                                                          # 'bg_color': 'yellow', 'color' : 'black',
                                                                          'text_wrap': True, 'shrink': True}),
                          'sub_heading_format_center': workbook.add_format({'align': 'center',
                                                                            'valign': 'vjustify',
                                                                            'bold': True, 'size': 9,
                                                                            'font_name': 'Times New Roman',
                                                                            # 'bg_color': 'yellow', 'color' : 'black',
                                                                            'text_wrap': True, 'shrink': True}),
                          'bold': workbook.add_format({'bold': True, 'font_name': 'Times New Roman',
                                                       'size': 11,
                                                       'text_wrap': True}),
                          'bold_center': workbook.add_format({'bold': True, 'font_name': 'Times New Roman',
                                                              'size': 11,
                                                              'text_wrap': True,
                                                              'align': 'center'}),
                          'date_format': workbook.add_format({'num_format': 'dd/mm/yyyy',
                                                              'font_name': 'Times New Roman', 'size': 11,
                                                              'align': 'center', 'text_wrap': True}),
                          'datetime_format': workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm:ss',
                                                                  'font_name': 'Times New Roman', 'size': 11,
                                                                  'align': 'center', 'text_wrap': True}),
                          'normal_format': workbook.add_format({'font_name': 'Times New Roman',
                                                                'size': 11, 'text_wrap': True}),
                          'normal_format_right': workbook.add_format({'font_name': 'Times New Roman',
                                                                      'align': 'right', 'size': 11,
                                                                      'text_wrap': True}),
                          'normal_format_central': workbook.add_format({'font_name': 'Times New Roman',
                                                                        'size': 11, 'align': 'center',
                                                                        'text_wrap': True}),
                          'amount_format': workbook.add_format({'num_format': '#,##0.00',
                                                                'font_name': 'Times New Roman',
                                                                'align': 'right', 'size': 11,
                                                                'text_wrap': True}),
                          'amount_format_2': workbook.add_format({'num_format': '#,##0.00',
                                                                  'font_name': 'Times New Roman',
                                                                  'bold': True,
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True}),
                          'amount_format_1': workbook.add_format({'num_format': '#,##0',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True}),
                          'normal_num_bold': workbook.add_format({'bold': True, 'num_format': '#,##0.00',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True}),
                          'float_rate_format': workbook.add_format({'num_format': '###0.000',
                                                                    'font_name': 'Times New Roman',
                                                                    'align': 'center', 'size': 11,
                                                                    'text_wrap': True}),
                          'int_rate_format': workbook.add_format({'num_format': '###0',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True})}
        # FORMATS END

        worksheet = workbook.add_worksheet("weekly_monthly")

        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 15)
        worksheet.set_column('I:I', 15)
        worksheet.set_column('J:J', 15)
        worksheet.set_column('K:K', 15)
        worksheet.set_column('L:L', 15)
        worksheet.set_column('M:M', 15)
        worksheet.set_column('N:N', 20)
        worksheet.set_column('O:O', 20)
        worksheet.set_column('P:P', 20)
        worksheet.set_column('Q:Q', 20)
        worksheet.set_column('R:R', 20)
        worksheet.set_column('S:S', 20)
        worksheet.set_column('T:T', 20)
        worksheet.set_column('U:U', 20)
        worksheet.set_column('V:V', 15)
        worksheet.set_column('W:W', 15)
        worksheet.set_column('X:X', 15)
        worksheet.set_column('Y:Y', 20)
        worksheet.set_column('Z:Z', 20)
        worksheet.set_column('AA:AA', 20)
        worksheet.set_column('AB:AB', 20)
        # worksheet.set_column(0, 0, 20)
        worksheet.merge_range('B1:G1', 'Weekly/Monthly Payout- QWY Technologies Pvt Ltd-INR',
                              design_formats['merged_format'])
        # worksheet.merge_range('A10:Z10 ', ' ', False)
        worksheet.set_row(0, 25)
        worksheet.set_row(8, 30)
        if active_model.name:
            worksheet.write(4, 1, 'Name', design_formats['heading_format_1'])
        if active_model.region_id.name:
            worksheet.write(5, 1, 'Region', design_formats['heading_format_1'])
        if active_model.from_date:
            worksheet.write(2, 1, 'From Date', design_formats['heading_format_2'])
        if active_model.to_date:
            worksheet.write(2, 5, 'To Date', design_formats['heading_format_2'])
        if active_model.description:
            worksheet.write(4, 5, 'Description', design_formats['heading_format_1'])
        if active_model.cashfree_ref:
            worksheet.write(5, 5, 'Cashfree Ref', design_formats['heading_format_1'])
        if active_model.transaction_date:
            worksheet.write(6, 5, 'Transfer Date', design_formats['heading_format_1'])
        if active_model.processed_date:
            worksheet.write(7, 5, 'Processed Date', design_formats['heading_format_1'])
        
        
        worksheet.write(8, 0, 'Transfer ID', design_formats['heading_format_2'])
        worksheet.write(8, 1, 'Driver ID', design_formats['heading_format_2'])
        worksheet.write(8, 2, 'Driver', design_formats['heading_format_2'])
        worksheet.write(8, 3, 'Account No', design_formats['heading_format_2'])
        worksheet.write(8, 4, 'IFSC', design_formats['heading_format_2'])
        worksheet.write(8, 5, 'Total No of Orders', design_formats['heading_format_2'])
        worksheet.write(8, 6, 'Driver Payouts', design_formats['heading_format_2'])
        worksheet.write(8, 7, 'Incentive', design_formats['heading_format_2'])
        worksheet.write(8, 8, 'Deduction', design_formats['heading_format_2'])
        worksheet.write(8, 9, 'TDS', design_formats['heading_format_2'])
        worksheet.write(8, 10, 'Total Payout', design_formats['heading_format_2'])
        worksheet.write(8, 11, 'Avg Cost Per Order', design_formats['heading_format_2'])
        worksheet.write(8, 12, 'Remarks', design_formats['heading_format_2'])
        worksheet.write(8, 13, 'Transaction Date', design_formats['heading_format_2'])
        worksheet.write(8, 14, 'Processed Date', design_formats['heading_format_2'])
        worksheet.write(8, 15, 'Payment Gateway Ref', design_formats['heading_format_2'])
        worksheet.write(8, 16, 'Status', design_formats['heading_format_2'])
        worksheet.write(8, 17, 'Payable Journal Entry', design_formats['heading_format_2'])
        worksheet.write(8, 18, 'Payment Journal Entry', design_formats['heading_format_2'])
        # worksheet.write(5, 12, 'Payment Journal entry', design_formats['heading_format_2'])

        worksheet.write(4, 2, active_model.name or '', design_formats['normal_format_central'])
        worksheet.write(5, 2, active_model.region_id.name or '', design_formats['normal_format_central'])
        worksheet.write(2, 2, active_model.from_date or '', design_formats['date_format'])
        worksheet.write(2, 6, active_model.to_date or '', design_formats['date_format'])
        worksheet.write(4, 6, active_model.description or '', design_formats['normal_format_central'])
        worksheet.write(5, 6, active_model.cashfree_ref or '', design_formats['normal_format_central'])
        worksheet.write(6, 6, active_model.transaction_date or '', design_formats['date_format'])
        worksheet.write(7, 6, active_model.processed_date or '', design_formats['date_format'])

        r = 9
        tot_pay = 0
        incen = 0
        bal_amt = 0
        tds_amt = 0
        fnl_pay = 0
        tot_order=0
        for line in active_model.batch_payout_line_ids:
            #             print('###############################', line.transfer_ref or '', line.employee_id.name)
            col = 0
            worksheet.write(r, col, line.transfer_id or '', design_formats['normal_format_central'])
            col += 1
            worksheet.write(r, col, line.driver_uid or '', design_formats['normal_format_central'])
            col += 1
            worksheet.write(r, col, line.employee_id.name or '', design_formats['normal_format_central'])
            col += 1
            worksheet.write(r, col, line.employee_id.account_no or '', design_formats['normal_format_central'])
            col += 1
            worksheet.write(r, col, line.employee_id.ifsc_code or '', design_formats['normal_format_central'])
            col += 1
            worksheet.write(r, col, sum(line.daily_payout_ids.mapped('no_of_orders')) or 0 , design_formats['normal_format_central'])
            col += 1
            tot_order+=sum(line.daily_payout_ids.mapped('no_of_orders')) or 0
            worksheet.write(r, col, line.daily_payout_amount or 0.00, design_formats['amount_format'])
            col += 1
            tot_pay = tot_pay + line.daily_payout_amount
            worksheet.write(r, col, line.incentive_amount or 0.00, design_formats['amount_format'])
            col += 1
            incen = incen + line.incentive_amount
            worksheet.write(r, col, line.deduction_amount or 0.00, design_formats['amount_format'])
            col += 1
            bal_amt = bal_amt + line.deduction_amount
            worksheet.write(r, col, line.tds_amount or 0.00, design_formats['amount_format'])
            col += 1
            tds_amt = tds_amt + line.tds_amount
            worksheet.write(r, col, line.total_payout or 0.00, design_formats['amount_format'])
            col += 1
            fnl_pay = fnl_pay + line.total_payout
            worksheet.write(r, col, line.avg_order_cost or 0.00, design_formats['amount_format'])
            col += 1
            worksheet.write(r, col, line.remarks or '', design_formats['normal_format_central'])
            col += 1
            worksheet.write(r, col, line.transaction_date or '', design_formats['date_format'])
            col += 1
            worksheet.write(r, col, line.processed_date or '', design_formats['date_format'])
            col += 1
            worksheet.write(r, col, line.cashfree_ref or '', design_formats['normal_format_central'])
            col += 1
            state = line.payment_state and dict(line._fields['payment_state'].selection).get(line.payment_state)
#             print("_____________state___________________________",state)
            worksheet.write(r, col, state or '', design_formats['normal_format_central'])
            col += 1
            worksheet.write(r, col, line.sudo().payable_journal_id and line.sudo().payable_journal_id.name or '', design_formats['normal_format_central'])
            col += 1
            worksheet.write(r, col, line.sudo().payment_journal_id and line.sudo().payment_journal_id.name or '', design_formats['normal_format_central'])
            r = r + 1
#         print('tot baln finl ##############################', tot_pay, bal_amt, fnl_pay, r)
        worksheet.write(r, 0, 'Total', design_formats['heading_format'])
        worksheet.write(r, 5, tot_order or 0.00, design_formats['heading_format'])
        worksheet.write(r, 6, tot_pay or 0.00, design_formats['amount_format_2'])
        worksheet.write(r, 7, incen or 0.00, design_formats['amount_format_2'])
        worksheet.write(r, 8, bal_amt or 0.00, design_formats['amount_format_2'])
        worksheet.write(r, 9, tds_amt or 0.00, design_formats['amount_format_2'])
        worksheet.write(r, 10, fnl_pay or 0.00, design_formats['amount_format_2'])
        if tot_order>0.00:
            worksheet.write(r, 11, (tot_pay+incen)/tot_order or 0.00, design_formats['amount_format_2'])
        else:
            worksheet.write(r, 11,  0.00, design_formats['amount_format_2'])
            