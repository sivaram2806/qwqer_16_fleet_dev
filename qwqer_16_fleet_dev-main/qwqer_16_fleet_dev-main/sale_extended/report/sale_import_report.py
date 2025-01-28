from operator import itemgetter
import json

import xlrd

from odoo import fields, models, api, _
import tempfile
import binascii
import base64
import certifi
import urllib3
import pytz
from datetime import datetime,timedelta,date
from dateutil import tz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare


import logging   
_logger = logging.getLogger(__name__)

class PayoutLinesXlsx(models.AbstractModel):
    _name = 'report.sale_extended.report_sales_import_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, active_model):
        # FORMATS STARTS
        design_formats = {'heading_format': workbook.add_format({'align': 'center',
                                                                 'valign': 'vcenter',
                                                                 'bold': True, 'size': 11,
                                                                 'font_name': 'Times New Roman',
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
                                                                   'bg_color': '#8080ff', 'color': 'black',
                                                                   'border': True,
                                                                   'text_wrap': True, 'shrink': True}),
                          'merged_format': workbook.add_format({'align': 'center',
                                                                'valign': 'vjustify',
                                                                'bold': True, 'size': 17,
                                                                'font_name': 'Times New Roman',
                                                                'text_wrap': True, 'shrink': True}),
                          'sub_heading_format': workbook.add_format({'align': 'right',
                                                                     'valign': 'vjustify',
                                                                     'bold': True, 'size': 9,
                                                                     'font_name': 'Times New Roman',
                                                                     'text_wrap': True, 'shrink': True}),
                          'sub_heading_format_left': workbook.add_format({'align': 'left',
                                                                          'valign': 'vjustify',
                                                                          'bold': False, 'size': 9,
                                                                          'font_name': 'Times New Roman',
                                                                          'text_wrap': True, 'shrink': True}),
                          'sub_heading_format_center': workbook.add_format({'align': 'center',
                                                                            'valign': 'vjustify',
                                                                            'bold': True, 'size': 9,
                                                                            'font_name': 'Times New Roman',
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

        worksheet = workbook.add_worksheet("Sale Import")

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
        worksheet.set_column('N:N', 15)
        worksheet.set_column('O:O', 15)
        worksheet.set_column('P:P', 15)
        worksheet.set_column('Q:Q', 15)
        worksheet.set_column('R:R', 15)
        worksheet.set_column('S:S', 15)
        worksheet.set_column('T:T', 15)
        worksheet.set_column('U:U', 15)
        worksheet.set_column('V:V', 15)
        worksheet.set_column('W:W', 15)
        worksheet.set_column('X:X', 15)
        worksheet.set_column('Y:Y', 15)
        worksheet.set_column('Z:Z', 15)
        worksheet.set_column('AA:AA', 15)
        

        
        worksheet.set_row(0, 50)
        worksheet.write(0, 0, 'Sl No', design_formats['heading_format_2'])
        worksheet.write(0, 1, 'Order Status', design_formats['heading_format_2'])
        worksheet.write(0, 2, 'Payment Mode', design_formats['heading_format_2'])
        worksheet.write(0, 3, 'Service Order Date(2022-04-30 09:51:42)', design_formats['heading_format_2'])
        worksheet.write(0, 4, 'Weight', design_formats['heading_format_2'])
        worksheet.write(0, 5, 'Est. Time', design_formats['heading_format_2'])
        worksheet.write(0, 6, 'Est. Dst.', design_formats['heading_format_2'])
        worksheet.write(0, 7, 'Order Amount', design_formats['heading_format_2'])
        worksheet.write(0, 8, 'Amount', design_formats['heading_format_2'])
        worksheet.write(0, 9, 'Discount', design_formats['heading_format_2'])
        worksheet.write(0, 10, 'Pricing Plan', design_formats['heading_format_2'])
        worksheet.write(0, 11, 'Driver ID', design_formats['heading_format_2'])
        worksheet.write(0, 12, 'To Name', design_formats['heading_format_2'])
        worksheet.write(0, 13, 'To Phone No', design_formats['heading_format_2'])
        worksheet.write(0, 14, 'To Address', design_formats['heading_format_2'])
        worksheet.write(0, 15, 'Pickup Distance', design_formats['heading_format_2'])
        worksheet.write(0, 16, 'Deliver Distance', design_formats['heading_format_2'])
        worksheet.write(0, 17, 'From Name', design_formats['heading_format_2'])
        worksheet.write(0, 18, 'From Phone No', design_formats['heading_format_2'])
        worksheet.write(0, 19, 'From Address', design_formats['heading_format_2'])
        worksheet.write(0, 20,'Sender Locality', design_formats['heading_format_2'])
        worksheet.write(0, 21, 'Order Source', design_formats['heading_format_2'])
        worksheet.write(0, 22, 'Payment Status', design_formats['heading_format_2'])
        worksheet.write(0, 23, 'Merchant Order ID', design_formats['heading_format_2'])
        worksheet.write(0, 24, 'Merchant Amount', design_formats['heading_format_2'])
        worksheet.write(0, 25, 'Merchant Payment Mode', design_formats['heading_format_2'])
        worksheet.write(0, 26, 'Quantity', design_formats['heading_format_2'])
        if self._context.get('download_failed_orders',False) and active_model.line_ids:
            file_string = tempfile.NamedTemporaryFile(suffix=".xlsx")
            file_string.write(binascii.a2b_base64(active_model.upload_file))
            book = xlrd.open_workbook(file_string.name)
            sheet = book.sheet_by_index(0)
            sl_no_list = active_model.line_ids.mapped('name')
            sl_no=1
            row = 1
            for el in range(sheet.nrows):
                if sheet.row_values(el) and sheet.row_values(el)[0] and sheet.row_values(el)[0] !='Sl No':
                    row_val=''
                    if isinstance(sheet.row_values(el)[0], float):
                        row_val=str(int(sheet.row_values(el)[0]))
                    elif isinstance(sheet.row_values(el)[0], int):
                        row_val=str(sheet.row_values(el)[0])
                    elif isinstance(sheet.row_values(el)[0], str):
                        row_val=sheet.row_values(el)[0]
                        
                    if  row_val and row_val in sl_no_list:
                    
                        worksheet.write(row, 0,  sheet.row_values(el)[0], design_formats['normal_format'])
                        worksheet.write(row, 1,  sheet.row_values(el)[1], design_formats['normal_format'])
                        worksheet.write(row, 2,  sheet.row_values(el)[2], design_formats['normal_format'])
                        worksheet.write(row, 3,  sheet.row_values(el)[3], design_formats['normal_format'])
                        worksheet.write(row, 4,  sheet.row_values(el)[4], design_formats['normal_format'])
                        worksheet.write(row, 5,  sheet.row_values(el)[5], design_formats['normal_format'])
                        worksheet.write(row, 6,  sheet.row_values(el)[6], design_formats['normal_format'])
                        worksheet.write(row, 7,  sheet.row_values(el)[7], design_formats['normal_format'])
                        worksheet.write(row, 8,  sheet.row_values(el)[8], design_formats['normal_format'])
                        worksheet.write(row, 9,  sheet.row_values(el)[9], design_formats['normal_format'])
                        worksheet.write(row, 10, sheet.row_values(el)[10], design_formats['normal_format'])
                        worksheet.write(row, 11, sheet.row_values(el)[11], design_formats['normal_format'])
                        worksheet.write(row, 12, sheet.row_values(el)[12], design_formats['normal_format'])
                        worksheet.write(row, 13, sheet.row_values(el)[13], design_formats['normal_format'])
                        worksheet.write(row, 14, sheet.row_values(el)[14], design_formats['normal_format'])
                        worksheet.write(row, 15, sheet.row_values(el)[15], design_formats['normal_format'])
                        worksheet.write(row, 16, sheet.row_values(el)[16], design_formats['normal_format'])
                        worksheet.write(row, 17, sheet.row_values(el)[17], design_formats['normal_format'])
                        worksheet.write(row, 18, sheet.row_values(el)[18], design_formats['normal_format'])
                        worksheet.write(row, 19, sheet.row_values(el)[19], design_formats['normal_format'])
                        worksheet.write(row, 20, sheet.row_values(el)[20], design_formats['normal_format'])
                        worksheet.write(row, 21, sheet.row_values(el)[21], design_formats['normal_format'])
                        worksheet.write(row, 22, sheet.row_values(el)[22], design_formats['normal_format'])
                        worksheet.write(row, 23, sheet.row_values(el)[23], design_formats['normal_format'])
                        worksheet.write(row, 24, sheet.row_values(el)[24], design_formats['int_rate_format'])
                        worksheet.write(row, 25, sheet.row_values(el)[25], design_formats['normal_format'])
                        worksheet.write(row, 26, sheet.row_values(el)[26], design_formats['int_rate_format'])
                        sl_no+=1
                        row+=1
        
