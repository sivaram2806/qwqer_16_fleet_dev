# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, _


class HdfcSalaryXls(models.AbstractModel):
    _name = 'report.payment_hdfc.hdfc_wo_adv_pay_export_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, active_model):
        # FORMATS STARTS
        design_formats = {'heading_format': workbook.add_format({'align': 'center',
                                                                 'valign': 'vcenter',
                                                                 'bold': True, 'size': 15,
                                                                 'font_name': 'Times New Roman',
                                                                 'text_wrap': True,
                                                                 'border': True,
                                                                 #                                                'bg_color': 'blue',
                                                                 #                                                'color' : 'white',
                                                                 'text_wrap': True, 'shrink': True}),
                          'heading_format_1': workbook.add_format({'align': 'left',
                                                                   'valign': 'vjustify',
                                                                   'bold': False, 'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   'border': True,
                                                                   #                                                'bg_color': 'blue',
                                                                   #                                                'color' : 'white',
                                                                   'text_wrap': True, 'shrink': True}),
                          'heading_format_2': workbook.add_format({'align': 'center',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   'border': True,
                                                                   #                                                'bg_color': 'blue',
                                                                   #                                                'color' : 'white',
                                                                   'text_wrap': True, 'shrink': True}),
                          'sub_heading_format': workbook.add_format({'align': 'right',
                                                                     'valign': 'vjustify',
                                                                     'bold': True, 'size': 9,
                                                                     'font_name': 'Times New Roman',
                                                                     #                                                    'bg_color': 'yellow',
                                                                     #                                                    'color' : 'black',
                                                                     'text_wrap': True, 'shrink': True}),
                          'sub_heading_format_left': workbook.add_format({'align': 'left',
                                                                          'valign': 'vjustify',
                                                                          'bold': False, 'size': 9,
                                                                          'font_name': 'Times New Roman',
                                                                          #                                                    'bg_color': 'yellow',
                                                                          #                                                    'color' : 'black',
                                                                          'text_wrap': True, 'shrink': True}),
                          'sub_heading_format_center': workbook.add_format({'align': 'center',
                                                                            'valign': 'vjustify',
                                                                            'bold': True, 'size': 9,
                                                                            'font_name': 'Times New Roman',
                                                                            #                                                    'bg_color': 'yellow',
                                                                            #                                                    'color' : 'black',
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
                                                                        'text_wrap': True,'border': True}),
                          'amount_format': workbook.add_format({'num_format': '###0',
                                                                'font_name': 'Times New Roman',
                                                                'align': 'center', 'size': 11,
                                                                'text_wrap': True,'border': True}),
                          'amount_format_1': workbook.add_format({'num_format': '#,##0',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True}),
                          'normal_num_bold': workbook.add_format({'bold': True, 'num_format': '#,##0.00',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True}),
                          'float_rate_format': workbook.add_format({'num_format': '###0.00',
                                                                    'font_name': 'Times New Roman',
                                                                    'align': 'right', 'size': 11,
                                                                    'text_wrap': True, 'border': True}),
                          'int_rate_format': workbook.add_format({'num_format': '###0',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True})}
        # FORMATS END

        worksheet = workbook.add_worksheet("HDFC Export")

        worksheet.set_column('A:A', 50)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 5)
        worksheet.set_column('G:G', 5)
        worksheet.set_column('H:H', 5)
        worksheet.set_column('I:I', 5)
        worksheet.set_column('J:J', 5)
        worksheet.set_column('K:K', 5)
        worksheet.set_column('L:L', 5)
        worksheet.set_column('M:M', 5)
        worksheet.set_column('N:N', 20)
        worksheet.set_column('O:O', 20)
        worksheet.set_column('P:P', 20)
        worksheet.set_column('Q:Q', 20)
        worksheet.set_column('R:R', 20)
        worksheet.set_column('S:S', 20)
        worksheet.set_column('T:T', 20)
        worksheet.set_column('U:U', 20)
        worksheet.set_column('V:V', 5)
        worksheet.set_column('W:W', 15)
        worksheet.set_column('X:X', 5)
        worksheet.set_column('Y:Y', 20)
        worksheet.set_column('Z:Z', 20)
        worksheet.set_column('AA:AA', 20)
        worksheet.set_column('AB:AB', 20)
        worksheet.set_column(0, 0, 20)
        worksheet.set_row(0, 50)
        worksheet.write(0, 0, '''Txn type\nRTGS - R\nNEFT - N\nHDFC TRF - I''', design_formats['heading_format_2'])
        worksheet.write(0, 1, 'Beneficiary Code\n(Mandatory only for txn type "I")', design_formats['heading_format_2'])
        worksheet.write(0, 2, 'Bene A/c No.', design_formats['heading_format_2'])
        worksheet.write(0, 3, 'Amount', design_formats['heading_format_2'])
        worksheet.write(0, 4, 'Beneficiary Name', design_formats['heading_format_2'])
        worksheet.write(0, 5, 'To be left Blank', design_formats['heading_format_2'])
        worksheet.write(0, 6, 'To be left Blank', design_formats['heading_format_2'])
        worksheet.write(0, 7, 'To be left Blank', design_formats['heading_format_2'])
        worksheet.write(0, 8, 'To be left Blank', design_formats['heading_format_2'])
        worksheet.write(0, 9, 'To be left Blank', design_formats['heading_format_2'])
        worksheet.write(0, 10, 'To be left Blank', design_formats['heading_format_2'])
        worksheet.write(0, 11, 'To be left Blank', design_formats['heading_format_2'])
        worksheet.write(0, 12, 'To be left Blank', design_formats['heading_format_2'])
        worksheet.write(0, 13, '''Customer Ref No\nonly for NEFT " N "''', design_formats['heading_format_2'])
        worksheet.write(0, 14, 'Payment Detail 1', design_formats['heading_format_2'])
        worksheet.write(0, 15, 'Payment Detail 2', design_formats['heading_format_2'])
        worksheet.write(0, 16, 'Payment Detail 3', design_formats['heading_format_2'])
        worksheet.write(0, 17, 'Payment Detail 4', design_formats['heading_format_2'])
        worksheet.write(0, 18, 'Payment Detail 5', design_formats['heading_format_2'])
        worksheet.write(0, 19, 'Payment Detail 6', design_formats['heading_format_2'])
        worksheet.write(0, 20, 'Payment Detail 7', design_formats['heading_format_2'])
        worksheet.write(0, 21, 'To be left Blank', design_formats['heading_format_2'])
        worksheet.write(0, 22, '''Inst. Date\nDD/MM/YYYY''', design_formats['heading_format_2'])
        worksheet.write(0, 23, 'To be left Blank', design_formats['heading_format_2'])
        worksheet.write(0, 24, 'IFSC code', design_formats['heading_format_2'])
        worksheet.write(0, 25, 'Bene Bank Name', design_formats['heading_format_2'])
        worksheet.write(0, 26, 'Bene Bank Branch Name', design_formats['heading_format_2'])
        worksheet.write(0, 27, 'Bene Email ID', design_formats['heading_format_2'])
        worksheet.write(0, 28, 'Payment Status', design_formats['heading_format_2'])
        worksheet.write(0, 29, 'Payment Date', design_formats['heading_format_2'])
        worksheet.write(0, 30, 'UTR Reference Number', design_formats['heading_format_2'])
        row = 1
        n = 1000

        for wo in active_model:
            for payment in wo.payment_ids:
                if payment.state == 'draft' and payment.journal_id.bank_name == 'hdfc' and payment.name not in ['/'] and payment.move_id.name not in ['/', 'Draft', 'Draft Payment']:
                    col = 0
                    txn_type = 'N'
                    if payment.partner_id.bank_name:
                        name_list = payment.partner_id.bank_name.split()
                        if 'HDFC' in name_list:
                            txn_type = 'I'

                    worksheet.write(row, col, txn_type, design_formats['normal_format_central'])
                    col += 1
                    if txn_type == 'I':
                        n = n + 1
                        worksheet.write(row, col, n, design_formats['normal_format_central'])
                    else:
                        worksheet.write(row, col, '', design_formats['normal_format_central'])
                    col += 1
                    worksheet.write(row, col, payment.partner_id.account_no or '', design_formats['normal_format_central'])
                    col += 1
                    worksheet.write(row, col, round(payment.amount,2), design_formats['float_rate_format'])
                    col += 1
                    if len(payment.partner_id.name) <= 15:
                        worksheet.write(row, col, payment.partner_id.name or '', design_formats['heading_format_1'])
                    else:
                        name = payment.partner_id.name
                        names = name[0:15]
                        worksheet.write(row, col, names or '', design_formats['heading_format_1'])
                    col += 1
                    worksheet.write(row, col,'', design_formats['heading_format_1'])
                    col += 1
                    worksheet.write(row, col,'', design_formats['heading_format_1'])
                    col += 1
                    worksheet.write(row, col,'', design_formats['heading_format_1'])
                    col += 1
                    worksheet.write(row, col,'', design_formats['heading_format_1'])
                    col += 1
                    worksheet.write(row, col,'', design_formats['heading_format_1'])
                    col += 1
                    worksheet.write(row, col,'', design_formats['heading_format_1'])
                    col += 1
                    worksheet.write(row, col,'', design_formats['heading_format_1'])
                    col += 1
                    worksheet.write(row, col,'', design_formats['heading_format_1'])
                    col += 1
                    if txn_type == 'I':
                        worksheet.write(row, col, '', design_formats['heading_format_1'])
                    else:
                        if len(payment.partner_id.name) <= 15:
                            worksheet.write(row, col, payment.partner_id.name or '', design_formats['normal_format_central'])
                        else:
                            name = payment.partner_id.name
                            names = name[0:15]
                            worksheet.write(row, col, names or '', design_formats['normal_format_central'])
                    col += 1
                    worksheet.write(row, col, wo.name or '', design_formats['heading_format_1'])
                    col += 1
                    worksheet.write(row, col, payment.name or '', design_formats['heading_format_1'])
                    col +=1
                    worksheet.write(row, col, wo.company_id.name or '', design_formats['heading_format_1'])
                    col +=1
                    worksheet.write(row, col, '', design_formats['heading_format_1'])
                    col +=1
                    worksheet.write(row, col, '', design_formats['heading_format_1'])
                    col +=1
                    worksheet.write(row, col, '', design_formats['heading_format_1'])
                    col +=1
                    worksheet.write(row, col, '', design_formats['heading_format_1'])
                    col +=1
                    worksheet.write(row, col, '', design_formats['heading_format_1'])
                    col +=1
                    date = datetime.now().strftime('%d/%m/%Y')
                    worksheet.write(row, col, date or '', design_formats['normal_format_central'])
                    col += 1
                    worksheet.write(row, col, '', design_formats['heading_format_1'])
                    col +=1
                    worksheet.write(row, col, payment.partner_id.ifsc_code or '', design_formats['heading_format_1'])
                    col += 1
                    worksheet.write(row, col, payment.partner_id.bank_name or '', design_formats['heading_format_1'])
                    col += 1
                    worksheet.write(row, col, '', design_formats['heading_format_1'])
                    col += 1
                    worksheet.write(row, col, payment.partner_id.email or 'accounts@qwytech.com', design_formats['heading_format_1'])
                    row += 1