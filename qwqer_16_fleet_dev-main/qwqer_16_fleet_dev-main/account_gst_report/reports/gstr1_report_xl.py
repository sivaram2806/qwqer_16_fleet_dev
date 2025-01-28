from odoo import models, fields
import logging
import datetime
from datetime import datetime
import pytz
import json
_logger = logging.getLogger('__name__')
import re
from collections import OrderedDict
import itertools


class SalespersonExcelReport(models.AbstractModel):
    _name = "report.account_gst_report.gstr1_report_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, obj):
        cell_text_format = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 10})
        cell_num_format = workbook.add_format({'align': 'right', 'bold': True, 'font_size': 10,'num_format': '#,##0.00'})
        format3 = workbook.add_format({'align': 'left', 'bold': False, 'font_size': 10})
        format_num = workbook.add_format({'align': 'right', 'bold': False, 'font_size': 10,'num_format': '#,##0.00'})
        head = workbook.add_format({'align': 'center', 'size': 12, 'bold': True})
        head2 = workbook.add_format({'align': 'center', 'size': 10, 'bold': True})
        head3 = workbook.add_format({'align': 'center', 'font_size': 10, 'bold': True, 'bg_color': '#808080'})
        date_format_header = workbook.add_format({'num_format': 'dd-mmm-yy','font_size': 10,
                                            'align': 'center', 'bold': True})
        date_format = workbook.add_format({'num_format': 'dd-mmm-yy','font_size': 10,
                                            'align': 'left'})
        worksheet1 = workbook.add_worksheet('B2B')
        worksheet2 = workbook.add_worksheet('B2C')
        worksheet3 = workbook.add_worksheet('CDNR')
        worksheet4 = workbook.add_worksheet('CDNUR')
        worksheet5 = workbook.add_worksheet('HSN')
        worksheet6 = workbook.add_worksheet('DOCS')
        worksheet7 = workbook.add_worksheet('B2C Invoice Details')
        company_name = self.env.user.company_id.name
        company_street = self.env.user.company_id.street or ''
        company_street2 = self.env.user.company_id.street2 or  ''
        company_city = self.env.user.company_id.city or ''
        company_zip = self.env.user.company_id.zip or ''
        company_addr = str(company_street + ' , ' + ' ' + company_street2 + '  ' + company_city + '  ' + company_zip)
        company_mob = self.env.user.company_id.phone or ''
        company_email = self.env.user.company_id.email or ''
        company_website = self.env.user.company_id.website or  ''
        if company_mob and company_email and company_website:
            company_addr1 = 'Ph:' + company_mob + ',' + ' ' + 'Email:' + company_email + ',' + ' ' + 'Website:' + company_website
        else:
            company_addr1 = ''
        worksheet1.set_column('A:A', 18)
        worksheet1.set_column('B:B', 25)
        worksheet1.set_column('C:C', 16)
        worksheet1.set_column('D:D', 12)
        worksheet1.set_column('E:E', 15)
        worksheet1.set_column('F:F', 15)
        worksheet1.set_column('G:G', 15)
        worksheet1.set_column('H:H', 8)
        worksheet1.set_column('I:I', 12)
        worksheet1.set_column('J:J', 8)
        worksheet1.set_column('K:K', 8)
        worksheet1.set_column('L:L', 8)

        worksheet1.merge_range('A1:F2', company_name, head)
        worksheet1.merge_range('A3:F4', company_addr, head2)
        worksheet1.merge_range('A5:F6', company_addr1, head2)

        worksheet2.set_column('A:A', 18)
        worksheet2.set_column('B:B', 25)
        worksheet2.set_column('C:C', 16)
        worksheet2.set_column('D:D', 12)
        worksheet2.set_column('E:E', 15)
        worksheet2.set_column('F:F', 15)
        worksheet2.set_column('G:G', 15)
        worksheet2.set_column('H:H', 8)
        worksheet2.merge_range('A1:F2', company_name, head)
        worksheet2.merge_range('A3:F4', company_addr, head2)
        worksheet2.merge_range('A5:F6', company_addr1, head2)
        
        worksheet3.set_column('A:A', 18)
        worksheet3.set_column('B:B', 25)
        worksheet3.set_column('C:C', 16)
        worksheet3.set_column('D:D', 12)
        worksheet3.set_column('E:E', 15)
        worksheet3.set_column('F:F', 15)
        worksheet3.set_column('G:G', 15)
        worksheet3.set_column('H:H', 15)
        worksheet3.set_column('I:I', 15)
        worksheet3.set_column('J:J', 15)
        worksheet3.set_column('K:K', 15)
        worksheet3.set_column('L:L', 15)
        worksheet3.set_column('M:M', 15)
        worksheet3.merge_range('A1:I2', company_name, head)
        worksheet3.merge_range('A3:I4', company_addr, head2)
        worksheet3.merge_range('A5:I6', company_addr1, head2)
        
        worksheet4.set_column('A:A', 18)
        worksheet4.set_column('B:B', 25)
        worksheet4.set_column('C:C', 16)
        worksheet4.set_column('D:D', 12)
        worksheet4.set_column('E:E', 15)
        worksheet4.set_column('F:F', 15)
        worksheet4.set_column('G:G', 15)
        worksheet4.set_column('H:H', 15)
        worksheet4.set_column('I:I', 15)
        worksheet4.set_column('J:J', 15)
        worksheet4.set_column('K:K', 15)
        worksheet4.set_column('L:L', 15)
        worksheet4.set_column('M:M', 15)
        worksheet4.merge_range('A1:I2', company_name, head)
        worksheet4.merge_range('A3:I4', company_addr, head2)
        worksheet4.merge_range('A5:I6', company_addr1, head2)
        
        worksheet5.set_column('A:A', 18)
        worksheet5.set_column('B:B', 25)
        worksheet5.set_column('C:C', 16)
        worksheet5.set_column('D:D', 12)
        worksheet5.set_column('E:E', 15)
        worksheet5.set_column('F:F', 15)
        worksheet5.set_column('G:G', 15)
        worksheet5.set_column('H:H', 15)
        worksheet5.set_column('I:I', 15)
        worksheet5.set_column('J:J', 15)
        worksheet5.set_column('K:K', 15)
        worksheet5.set_column('L:L', 15)
        worksheet5.set_column('M:M', 15)
        worksheet5.merge_range('A1:I2', company_name, head)
        worksheet5.merge_range('A3:I4', company_addr, head2)
        worksheet5.merge_range('A5:I6', company_addr1, head2)
        
        worksheet6.set_column('A:A', 30)
        worksheet6.set_column('B:B', 25)
        worksheet6.set_column('C:C', 16)
        worksheet6.set_column('D:D', 12)
        worksheet6.set_column('E:E', 15)
        worksheet6.set_column('F:F', 15)
        worksheet6.set_column('G:G', 15)
        worksheet6.set_column('H:H', 15)
        worksheet6.set_column('I:I', 15)
        worksheet6.set_column('J:J', 15)
        worksheet6.set_column('K:K', 15)
        worksheet6.set_column('L:L', 15)
        worksheet6.set_column('M:M', 15)
        worksheet6.merge_range('A1:I2', company_name, head)
        worksheet6.merge_range('A3:I4', company_addr, head2)
        worksheet6.merge_range('A5:I6', company_addr1, head2)
        
        worksheet7.set_column('A:A', 30)
        worksheet7.set_column('B:B', 25)
        worksheet7.set_column('C:C', 16)
        worksheet7.set_column('D:D', 12)
        worksheet7.set_column('E:E', 15)
        worksheet7.set_column('F:F', 15)
        worksheet7.set_column('G:G', 15)
        worksheet7.set_column('H:H', 15)
        worksheet7.set_column('I:I', 15)
        worksheet7.set_column('J:J', 15)
        worksheet7.set_column('K:K', 15)
        worksheet7.set_column('L:L', 15)
        worksheet7.set_column('M:M', 15)
        worksheet7.merge_range('A1:I2', company_name, head)
        worksheet7.merge_range('A3:I4', company_addr, head2)
        worksheet7.merge_range('A5:I6', company_addr1, head2)
        
        row1 = 7
        row2 = 7
        row3 = 7
        row4 = 7
        row5 = 7
        row6 = 7
        row7 = 7
        column = 0

        worksheet1.merge_range('B7:E7', 'GST Report', head)
        worksheet2.merge_range('B7:E7', 'GST Report', head)
        worksheet3.merge_range('B7:H7', 'GST Report', head)
        worksheet4.merge_range('B7:H7', 'GST Report', head)
        worksheet5.merge_range('B7:H7', 'GST Report', head)
        worksheet6.merge_range('B7:H7', 'GST Report', head)
        worksheet7.merge_range('B7:H7', 'B2C Invoice Details', head)

        row1 += 2
        row2 += 2
        row3 += 2
        row4 += 2
        row5 += 2
        row6 += 2
        row7 += 2
        print(data)
        from_date = fields.Date.from_string(data['from_date']).strftime('%d-%b-%y')
        DATETIME_FORMAT = "%d-%b-%y"
        f_date = datetime.strptime(from_date, DATETIME_FORMAT)
        print("from date type ------------------- ",type(from_date),type(f_date))
        to_date = fields.Date.from_string(data['to_date']).strftime('%d-%b-%y')
        t_date = datetime.strptime(to_date, DATETIME_FORMAT)

        worksheet1.write(row1, column, 'From Date', cell_text_format)
        worksheet1.write(row1, column + 1, f_date, date_format_header)
        worksheet1.write(row1, column + 3, 'To Date', cell_text_format)
        worksheet1.write(row1, column + 4, t_date, date_format_header)

        worksheet2.write(row2, column, 'From Date', cell_text_format)
        worksheet2.write(row2, column + 1, f_date, date_format_header)
        worksheet2.write(row2, column + 3, 'To Date', cell_text_format)
        worksheet2.write(row2, column + 4, t_date, date_format_header)
        
        worksheet3.write(row3, column, 'From Date', cell_text_format)
        worksheet3.write(row3, column + 1, f_date, date_format_header)
        worksheet3.write(row3, column + 3, 'To Date', cell_text_format)
        worksheet3.write(row3, column + 4, t_date, date_format_header)
        
        worksheet4.write(row4, column, 'From Date', cell_text_format)
        worksheet4.write(row4, column + 1, f_date, date_format_header)
        worksheet4.write(row4, column + 3, 'To Date', cell_text_format)
        worksheet4.write(row4, column + 4, t_date, date_format_header)
        
        worksheet5.write(row5, column, 'From Date', cell_text_format)
        worksheet5.write(row5, column + 1, f_date, date_format_header)
        worksheet5.write(row5, column + 3, 'To Date', cell_text_format)
        worksheet5.write(row5, column + 4, t_date, date_format_header)
        
        worksheet6.write(row6, column, 'From Date', cell_text_format)
        worksheet6.write(row6, column + 1, f_date, date_format_header)
        worksheet6.write(row6, column + 3, 'To Date', cell_text_format)
        worksheet6.write(row6, column + 4, t_date, date_format_header)
        
        worksheet7.write(row6, column, 'From Date', cell_text_format)
        worksheet7.write(row6, column + 1, f_date, date_format_header)
        worksheet7.write(row6, column + 3, 'To Date', cell_text_format)
        worksheet7.write(row6, column + 4, t_date, date_format_header)
        
        row3 += 2
        row4 += 2
        worksheet3.write(row3, column, 'No. of Recipients', cell_text_format)
        worksheet3.write(row3, column + 1, 'No. of Invoices', cell_text_format)
        worksheet3.write(row3, column + 3, 'No. of Notes/Vouchers', cell_text_format)
        worksheet3.write(row3, column + 8, 'Total Note/Refund Voucher Value', cell_text_format)
        worksheet3.write(row3, column + 10, 'Total Taxable Value', cell_text_format)
        worksheet3.write(row3, column + 11, 'Total Cess', cell_text_format)
        row_cdnr = row3 + 1

        worksheet4.write(row4, column, '', cell_text_format)
        worksheet4.write(row4, column + 1, 'No. of Notes/Vouchers', cell_text_format)
        worksheet4.write(row4, column + 4, 'No. of Invoices', cell_text_format)
        worksheet4.write(row4, column + 8, 'Total Note Value', cell_text_format)
        worksheet4.write(row4, column + 10, 'Total Taxable Value', cell_text_format)
        worksheet4.write(row4, column + 11, 'Total Cess', cell_text_format)

        row3 += 2
        
        row5 += 2
        row6 += 2
        worksheet5.write(row5, column, 'No. of HSN', cell_text_format)
        worksheet5.write(row5, column + 4, 'Total Value', cell_text_format)
        worksheet5.write(row5, column + 5, 'Total Taxable Value', cell_text_format)
        worksheet5.write(row5, column + 6, 'Total Integrated Tax', cell_text_format)
        worksheet5.write(row5, column + 7, 'Total Central Tax', cell_text_format)
        worksheet5.write(row5, column + 8, 'Total State/UT Tax', cell_text_format)
        worksheet5.write(row5, column + 9, 'Total Cess', cell_text_format)
        row_hsn = row5 + 1
        row5 += 2
        
        row5 += 2
        worksheet6.write(row6, column + 3, 'Total Number', cell_text_format)
        worksheet6.write(row6, column + 4, 'Total Cancelled', cell_text_format)
        
        row_hsn = row5 + 1
        row5 += 2

        row1 += 2
        row2 += 2
        row3 += 2
        row4 += 2

        row5 += 2
        row6 += 2
        row7 += 2
        worksheet1.write(row1, column, 'GSTIN/UIN of Recipient', cell_text_format)
        worksheet1.write(row1, column + 1, 'Receiver Name', cell_text_format)
        worksheet1.write(row1, column + 2, 'Invoice Number', cell_text_format)
        worksheet1.write(row1, column + 3, 'HSN code', cell_text_format)
        worksheet1.write(row1, column + 4, 'Invoice Date', cell_text_format)
        worksheet1.write(row1, column + 5, 'Invoice Value', cell_text_format)
        worksheet1.write(row1, column + 6, 'Place of supply', cell_text_format)
        worksheet1.write(row1, column + 7, 'Reverse Charge', cell_text_format)
        worksheet1.write(row1, column + 8, 'Rate', cell_text_format)
        worksheet1.write(row1, column + 9, 'Taxable value', cell_text_format)
        worksheet1.write(row1, column + 10, 'KFC %', cell_text_format)
        worksheet1.write(row1, column + 11, 'IGST %', cell_text_format)
        worksheet1.write(row1, column + 12, 'CGST %', cell_text_format)
        worksheet1.write(row1, column + 13, 'SGST %', cell_text_format)
        worksheet1.write(row1, column + 14, 'KFC Amount', cell_text_format)
        worksheet1.write(row1, column + 15, 'IGST Amount', cell_text_format)
        worksheet1.write(row1, column + 16, 'CGST Amount', cell_text_format)
        worksheet1.write(row1, column + 17, 'SGST Amount', cell_text_format)
        worksheet2.write(row2, column, 'Type', cell_text_format)
        worksheet2.write(row2, column + 1, 'Place of supply', cell_text_format)
        worksheet2.write(row2, column + 2, 'HSN Code', cell_text_format)
        worksheet2.write(row2, column + 3, 'Invoice Value', cell_text_format)
        worksheet2.write(row2, column + 4, 'Taxable value', cell_text_format)
        worksheet2.write(row2, column + 5, 'KFC Amount', cell_text_format)
        worksheet2.write(row2, column + 6, 'IGST Amount', cell_text_format)
        worksheet2.write(row2, column + 7, 'CGST Amount', cell_text_format)
        worksheet2.write(row2, column + 8, 'SGST Amount', cell_text_format)
        
        
                                                                                                            
        
        worksheet3.write(row3, column, 'GSTIN/UIN of Recipient', cell_text_format)
        worksheet3.write(row3, column + 1, 'Invoice/Advance Receipt Number', cell_text_format)
        worksheet3.write(row3, column + 2, 'Receipt Name', cell_text_format)
        worksheet3.write(row3, column + 3, 'Invoice/Advance Receipt date', cell_text_format)
        worksheet3.write(row3, column + 4, 'Note/Refund Voucher Number', cell_text_format)
        worksheet3.write(row3, column + 5, 'Note/Refund Voucher date', cell_text_format)
        worksheet3.write(row3, column + 6, 'Document Type', cell_text_format)
        worksheet3.write(row3, column + 7, 'Reason For Issuing document', cell_text_format)
        worksheet3.write(row3, column + 8, 'Place Of Supply', cell_text_format)
        worksheet3.write(row3, column + 9, 'Note/Refund Voucher Value', cell_text_format)
        worksheet3.write(row3, column + 10, 'Rate', cell_text_format)
        worksheet3.write(row3, column + 11, 'Taxable Value', cell_text_format)
        worksheet3.write(row3, column + 12, 'Cess Amount', cell_text_format)
        worksheet3.write(row3, column + 13, 'Pre GST', cell_text_format)
        
        worksheet4.write(row4, column, 'UR Type', cell_text_format)
        worksheet4.write(row4, column + 1, 'Note/Refund Voucher Number', cell_text_format)
        worksheet4.write(row4, column + 2, 'Note/Refund Voucher date', cell_text_format)
        worksheet4.write(row4, column + 3, 'Document Type', cell_text_format)
        worksheet4.write(row4, column + 4, 'Invoice/Advance Receipt Number', cell_text_format)
        worksheet4.write(row4, column + 5, 'Invoice/Advance Receipt date', cell_text_format)
        worksheet4.write(row4, column + 6, 'Reason For Issuing document', cell_text_format)
        worksheet4.write(row4, column + 7, 'Place Of Supply', cell_text_format)
        worksheet4.write(row4, column + 8, 'Note/Refund Voucher Value', cell_text_format)
        worksheet4.write(row4, column + 9, 'Rate', cell_text_format)
        worksheet4.write(row4, column + 10, 'Taxable Value', cell_text_format)
        worksheet4.write(row4, column + 11, 'Cess Amount', cell_text_format)
        worksheet4.write(row4, column + 12, 'Pre GST', cell_text_format)
        
        worksheet5.write(row5, column, 'HSN', cell_text_format)
        worksheet5.write(row5, column + 1, 'Description', cell_text_format)
        worksheet5.write(row5, column + 2, 'UQC', cell_text_format)
        worksheet5.write(row5, column + 3, 'Total Quantity', cell_text_format)
        worksheet5.write(row5, column + 4, 'Total Value', cell_text_format)
        worksheet5.write(row5, column + 5, 'Taxable Value', cell_text_format)
        worksheet5.write(row5, column + 6, 'Integrated Tax Amount', cell_text_format)
        worksheet5.write(row5, column + 7, 'Central Tax Amount', cell_text_format)
        worksheet5.write(row5, column + 8, 'State/UT Tax Amount', cell_text_format)
        worksheet5.write(row5, column + 9, 'Cess Amount', cell_text_format)
        
        worksheet6.write(row6, column, 'Nature  of Document', cell_text_format)
        worksheet6.write(row6, column + 1, 'Sr. No. From', cell_text_format)
        worksheet6.write(row6, column + 2, 'Sr. No. To', cell_text_format)
        worksheet6.write(row6, column + 3, 'Total Number', cell_text_format)
        worksheet6.write(row6, column + 4, 'Cancelled', cell_text_format)
        
        
        worksheet7.write(row7, column, 'Invoice Number', cell_text_format)
        worksheet7.write(row7, column + 1, 'Invoice Date', cell_text_format)
        worksheet7.write(row7, column + 2, 'Invoice Value', cell_text_format)
        worksheet7.write(row7, column + 3, 'Place of supply', cell_text_format)
        worksheet7.write(row7, column + 4, 'HSN code', cell_text_format)
        worksheet7.write(row7, column + 5, 'Taxable value', cell_text_format)
        worksheet7.write(row7, column + 6, 'KFC Amount', cell_text_format)
        worksheet7.write(row7, column + 7, 'IGST Amount', cell_text_format)
        worksheet7.write(row7, column + 8, 'CGST Amount', cell_text_format)
        worksheet7.write(row7, column + 9, 'SGST Amount', cell_text_format)
        
        
        

        b2b = []
        b2c = []
        b2c_list = []
        cdnr = []
        cdnur = []
        hsn=[]
        doc=[]
        place_of_supply_list = []
        domain = [('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]
        cdnr_domain = [('move_type', '=', 'out_refund'), ('state', '=', 'posted')]
        cdnur_domain = [('move_type', '=', 'out_refund'), ('state', '=', 'posted')]
        hsn_domain=[('move_type', 'in', ['out_invoice','out_refund']), ('state', '=', 'posted')]
        doc_domain=[('move_type', '=', 'out_invoice'),('state', '!=', 'draft')]
        doc_domain1=[('move_type', '=', 'out_refund'),('state', '!=', 'draft')]
        service_type = self.env['partner.service.type'].search([('id', '=', data['service_type'][0])])
        
        if data['service_type']:
            if service_type.is_fleet_service or service_type.is_qshop_service:
                domain.append(('service_type_id','=',service_type.id))
                cdnr_domain.append(('service_type_id','=',service_type.id))
                cdnur_domain.append(('service_type_id','=',service_type.id))
                hsn_domain.append(('service_type_id','=',service_type.id))
                doc_domain.append(('service_type_id','=',service_type.id))
                doc_domain1.append(('service_type_id','=',service_type.id))
            else:
                domain.append(('service_type_id','in',[service_type.id,False]))
                cdnr_domain.append(('service_type_id','in',[service_type.id,False]))
                cdnur_domain.append(('service_type_id','in',[service_type.id,False]))
                hsn_domain.append(('service_type_id','in',[service_type.id,False]))
                doc_domain.append(('service_type_id','in',[service_type.id,False]))
                doc_domain1.append(('service_type_id','in',[service_type.id,False]))

            

        if data['from_date']:
            domain.append(('invoice_date', '>=', data['from_date']))
            cdnr_domain.append(('invoice_date', '>=', data['from_date']))
            cdnur_domain.append(('invoice_date', '>=', data['from_date']))
            hsn_domain.append(('invoice_date', '>=', data['from_date']))
            doc_domain.append(('invoice_date', '>=', data['from_date']))
            doc_domain1.append(('invoice_date', '>=', data['from_date']))

        if data['to_date']:
            domain.append(('invoice_date', '<=', data['to_date']))
            cdnr_domain.append(('invoice_date', '<=', data['to_date']))
            cdnur_domain.append(('invoice_date', '<=', data['to_date']))
            hsn_domain.append(('invoice_date', '<=', data['to_date']))
            doc_domain.append(('invoice_date', '<=', data['to_date']))
            doc_domain1.append(('invoice_date', '<=', data['to_date']))

        if data['state_ids']:


            state_journal = self.env['state.journal'].search([('state_id','in',data['state_ids'])])
            state_journal_list = []
            for i in state_journal:
                if service_type.is_fleet_service:
                    if i.fleet_journal_id.id not in state_journal_list:
                        state_journal_list.append(i.fleet_journal_id.id)
                elif service_type.is_qshop_service:
                    if i.qshop_journal_id.id not in state_journal_list:
                        state_journal_list.append(i.qshop_journal_id.id)
                else:
                    if i.delivery_journal_id.id not in state_journal_list:
                        state_journal_list.append(i.delivery_journal_id.id)

                
            domain.append(('journal_id', 'in', state_journal_list))
            cdnr_domain.append(('journal_id', 'in', state_journal_list))
            cdnur_domain.append(('journal_id', 'in', state_journal_list))
            hsn_domain.append(('journal_id', 'in', state_journal_list))
            doc_domain.append(('journal_id', 'in', state_journal_list))
            doc_domain1.append(('journal_id', 'in', state_journal_list))

        moves = self.env['account.move'].search(domain)
        cdnr_moves = self.env['account.move'].search(cdnr_domain)
        hsn_moves=self.env['account.move'].search(hsn_domain)
        doc_moves=self.env['account.move'].search(doc_domain)
        doc_moves1=self.env['account.move'].search(doc_domain1)
        for mov in moves:
            product_ids = mov.invoice_line_ids.mapped('product_id') or False
            hsn_code = product_ids and product_ids[0].l10n_in_hsn_code or '996813'
            gst = mov.partner_id.vat or False
            
            tax_account = [] 
            tax_rate_list = False 
            tax_list_rec = mov.invoice_line_ids.mapped('tax_ids')
            for tax in tax_list_rec:
                if tax.amount_type == 'group':
                    tax_account.append(tax.children_tax_ids.invoice_repartition_line_ids.mapped('account_id'))
                    tax_rate_list = tax.children_tax_ids.mapped('amount')
                elif tax.amount_type == 'percent':
                    tax_account.append(tax.invoice_repartition_line_ids.mapped('account_id'))
                    tax_rate_list = tax.mapped('amount')
            tax_account = list(set(list(itertools.chain(*tax_account))))   
            tax_line_list = mov.line_ids.filtered(lambda st: st.account_id in tax_account)
            tax_rate = 0
            if tax_rate_list:
                for ele in range(0, len(tax_rate_list)):
                    tax_rate = tax_rate + tax_rate_list[ele]
                    
                    
            
            if gst:
                place_of_supply = mov.partner_id.state_id.name
                if mov.partner_id.state_id.l10n_in_tin:
                    place_of_supply = mov.partner_id.state_id.l10n_in_tin + "-" +mov.partner_id.state_id.name
                dict = {
                    'gst_no': gst,
                    'receiver': mov.partner_id.name,
                    'inv_no': mov.name,
                    'place': place_of_supply,
                    'inv_date': datetime.strptime(mov.invoice_date.strftime('%d-%b-%y'), DATETIME_FORMAT),
                    'inv_value': mov.amount_total,
                    'hsn':hsn_code or '996813',
                    'cgst': 0.00,
                    'sgst': 0.00,
                    'igst': 0.00,
                    'kfc': 0.00,
                    'igst_amount':0.00,
                    'cgst_amount':0.00,
                    'sgst_amount':0.00,
                    'kfc_amount':0.00,
                    'rate': 0.00,
                    'untaxed_amt': mov.amount_untaxed,
                    }
            
                b2b.append(dict)
                if tax_line_list: 
                    for i in tax_line_list:
                        tax_name = i.tax_line_id.name
                        tax = i.tax_line_id
                        if 'KFC' in tax_name:
                            dict.update({'kfc': tax.amount})
                            dict.update({'kfc_amount': dict['kfc_amount'] + abs(i.balance)})
                        if 'CGST' in tax_name:
                            dict.update({'cgst': tax.amount})
                            dict.update({'cgst_amount': dict['cgst_amount'] + abs(i.balance)})
                            dict.update({'rate': tax_rate})
                        if 'SGST' in tax_name:
                            dict.update({'sgst': tax.amount})
                            dict.update({'sgst_amount': dict['sgst_amount'] + abs(i.balance)})
                            dict.update({'rate': tax_rate})
                        if 'IGST' in tax_name:
                            dict.update({'igst': tax.amount})
                            dict.update({'igst_amount': dict['igst_amount'] + abs(i.balance)})
                            dict.update({'rate': tax_rate})
            if not gst :
                taxes={}
                place_of_supply = mov.partner_id.state_id.name
                if mov.partner_id.state_id.l10n_in_tin:
                    place_of_supply = mov.partner_id.state_id.l10n_in_tin + "-" +mov.partner_id.state_id.name
                
                b2c_dict = {
                    'inv_no': mov.name,
                    'inv_date': datetime.strptime(mov.invoice_date.strftime('%d-%b-%y'), DATETIME_FORMAT),
                    'inv_value': mov.amount_total,
                    'place': place_of_supply,
                    'cgst': 0.00,
                    'sgst': 0.00,
                    'igst': 0.00,
                    'kfc': 0.00,
                    'hsn':hsn_code,
                    'igst_amount':0.00,
                    'cgst_amount':0.00,
                    'sgst_amount':0.00,
                    'kfc_amount':0.00,
                    'rate': 0.00,
                    'untaxed_amt': mov.amount_untaxed,
                }
                b2c_list.append(b2c_dict)
                
                if tax_line_list: 
                    for i in tax_line_list:
                        tax_name = i.tax_line_id.name
                        tax = i.tax_line_id
                        if 'KFC' in tax_name:
                            b2c_dict.update({'kfc_amount': b2c_dict['kfc_amount'] + abs(i.balance)})
                        if 'CGST' in tax_name:
                            b2c_dict.update({'cgst_amount': b2c_dict['cgst_amount'] + abs(i.balance)})
                        if 'SGST' in tax_name:
                            b2c_dict.update({'sgst_amount': b2c_dict['sgst_amount'] + abs(i.balance)})
                        if 'IGST' in tax_name:
                            b2c_dict.update({'igst_amount': b2c_dict['igst_amount'] + abs(i.balance)})
                place_id = mov.partner_id.state_id.id
                if not any(ls['place_id'] == place_id for ls in b2c):
                    dict2 = {
                        'receiver': mov.partner_id.name,
                        'inv_no': mov.name,
                        'place_id': place_id,
                        'place': place_of_supply,
                        'inv_date': datetime.strptime(mov.invoice_date.strftime('%d-%b-%y'), DATETIME_FORMAT),
                        'inv_value': mov.amount_total,
                        'hsn':hsn_code,
                        'cgst': 0.00,
                        'kfc_b2c': 0.00,
                        'igst_amount':0.00,
                        'cgst_amount':0.00,
                        'sgst_amount':0.00,
                        'kfc_amount':0.00,
                        'sgst': 0.00,
                        'igst': 0.00,
                        'rate': 0.00,
                        'untaxed_amt': mov.amount_untaxed,
                    }
                    b2c.append(dict2)
                    if tax_line_list: 
                        for i in tax_line_list:
                            tax_name = i.tax_line_id.name
                            tax = i.tax_line_id
                            if 'KFC' in tax_name:
                                dict2.update({'kfc_b2c':tax.amount})
                                dict2.update({'kfc_amount': dict2['kfc_amount']+abs(i.balance)})
                            if 'CGST' in tax_name:
                                dict2.update({'cgst': tax.amount})
                                dict2.update({'cgst_amount': dict2['cgst_amount']+abs(i.balance)})
                                dict2.update({'rate': tax_rate})
                            if 'SGST' in tax_name:
                                dict2.update({'sgst': tax.amount})
                                dict2.update({'sgst_amount': dict2['sgst_amount']+abs(i.balance)})
                                dict2.update({'rate': tax_rate})
                            if 'IGST' in tax_name:
                                dict2.update({'igst': tax.amount})
                                dict2.update({'igst_amount': dict2['igst_amount']+abs(i.balance)})
                                dict2.update({'rate': tax_rate})
                elif not any(ls['hsn'] == hsn_code and ls['place_id'] == place_id for ls in b2c):
                    dict2 = {
                            'receiver': mov.partner_id.name,
                            'inv_no': mov.name,
                            'place_id': place_id,
                            'place': place_of_supply,
                            'inv_date': datetime.strptime(mov.invoice_date.strftime('%d-%b-%y'), DATETIME_FORMAT),
                            'inv_value': mov.amount_total,
                            'hsn':hsn_code,
                            'cgst': 0.00,
                            'kfc_b2c': 0.00,
                            'igst_amount':0.00,
                            'cgst_amount':0.00,
                            'sgst_amount':0.00,
                            'kfc_amount':0.00,
                            'sgst': 0.00,
                            'igst': 0.00,
                            'rate': 0.00,
                            'untaxed_amt': mov.amount_untaxed,
                        }
                    b2c.append(dict2)
                    if tax_line_list: 
                        for tax_line in tax_line_list:
                            tax_name = tax_line.tax_line_id.name
                            tax = tax_line.tax_line_id
                            if 'KFC' in tax_name:
                                dict2.update({'kfc_b2c':tax.amount})
                                dict2.update({'kfc_amount': dict2['kfc_amount']+abs(tax_line.balance)})
                            if 'CGST' in tax_name:
                                dict2.update({'cgst': tax.amount})
                                dict2.update({'cgst_amount': dict2['cgst_amount']+abs(tax_line.balance)})
                                dict2.update({'rate': tax_rate})
                            if 'SGST' in tax_name:
                                dict2.update({'sgst': tax.amount})
                                dict2.update({'sgst_amount': dict2['sgst_amount']+abs(tax_line.balance)})
                                dict2.update({'rate': tax_rate})
                            if 'IGST' in tax_name:
                                dict2.update({'igst': tax.amount})
                                dict2.update({'igst_amount': dict2['igst_amount']+abs(tax_line.balance)})
                                dict2.update({'rate': tax_rate})
                                
                                
                                
                else:
                    for i in b2c:
                        if i['place_id'] == place_id:
                            if i['hsn'] == hsn_code:
                                i.update({'inv_value': i['inv_value'] + mov.amount_total,
                                          'untaxed_amt': i['untaxed_amt'] + mov.amount_untaxed,
                                          })
                                
                                if tax_line_list: 
                                    for x in tax_line_list:
                                        tax_name = x.tax_line_id.name
                                        tax = x.tax_line_id
                                        if 'KFC' in tax_name:
                                            i.update({'kfc_b2c': i['kfc_b2c']+ tax.amount})
                                            i.update({'kfc_amount': i['kfc_amount']+abs(x.balance)})
                                        if 'CGST' in tax_name:
                                            i.update({'cgst': i['cgst'] + tax.amount})
                                            i.update({'cgst_amount':i['cgst_amount']+ abs(x.balance)})
                                            i.update({'rate': tax_rate})
                                        if 'SGST' in tax_name:
                                            i.update({'sgst': i['sgst'] + tax.amount})
                                            i.update({'sgst_amount':i['sgst_amount'] +abs(x.balance)})
                                            i.update({'rate': tax_rate})
                                        if 'IGST' in tax_name:
                                            i.update({'igst': i['igst'] + tax.amount})
                                            i.update({'igst_amount':i['igst_amount']+ abs(x.balance)})
                                            i.update({'rate': tax_rate})

        vat_list = []
        inv_list = []
        refund_list = []
        total_refund = 0.0
        total_taxable_val = 0.0
        total_cess = 0.0
        for mov in cdnr_moves:
            gst = mov.partner_id.vat or False
            if gst:
                reversed_move = self.env['account.move'].search([('id','=',mov.reversed_entry_id.id)])
                inv_date = ""
                refund_date = ""
                if reversed_move.invoice_date:
                    inv_date = datetime.strptime(reversed_move.invoice_date.strftime('%d-%b-%y'), DATETIME_FORMAT)
                if mov.invoice_date:
                    refund_date = datetime.strptime(mov.invoice_date.strftime('%d-%b-%y'), DATETIME_FORMAT)    
                rate = 0.00
                for line in mov.invoice_line_ids:
                    place_of_supply = mov.partner_id.state_id.name
                    if mov.partner_id.state_id.l10n_in_tin:
                        place_of_supply = mov.partner_id.state_id.l10n_in_tin + "-" +mov.partner_id.state_id.name
                    vat_list.append(gst)
                    inv_list.append(reversed_move.name)
                    refund_list.append(mov.name)
                    total_refund += mov.amount_total
                    total_taxable_val += mov.amount_untaxed
                    dict = {
                        'gst_no': gst,
                        'inv_no': reversed_move.name,
                        'inv_date': inv_date,
                        'refund_no':mov.name,
                        'refund_date': refund_date,
                        'doc_type':"C",
                        'reason':'04-Correction in Invoice',
                        'receiver': mov.partner_id.name,
                        'place': place_of_supply,
                        'refund_value': mov.amount_total,
                        'rate': rate,
                        'untaxed_amt': mov.amount_untaxed,
                        'pre_gst':'N'
                    }
                cdnr.append(dict)

            if not gst:
                reversed_move = self.env['account.move'].search([('id','=',mov.reversed_entry_id.id)])
                inv_date = ""
                refund_date = ""
                if reversed_move.invoice_date:
                    inv_date = datetime.strptime(reversed_move.invoice_date.strftime('%d-%b-%y'), DATETIME_FORMAT)
                if mov.invoice_date:
                    refund_date = datetime.strptime(mov.invoice_date.strftime('%d-%b-%y'), DATETIME_FORMAT)    
                for line in mov.invoice_line_ids:
                    place_of_supply = mov.partner_id.state_id.name
                    if mov.partner_id.state_id.l10n_in_tin:
                        place_of_supply = mov.partner_id.state_id.l10n_in_tin + "-" +mov.partner_id.state_id.name
                    dict = {
                        'ur_type':'B2CL',
                        'gst_no': '',
                        'inv_no': reversed_move.name,
                        'inv_date': inv_date,
                        'refund_no':mov.name,
                        'refund_date': refund_date,
                        'doc_type':"C",
                        'reason':'04-Correction in Invoice',
                        'receiver': mov.partner_id.name,
                        'place': place_of_supply,
                        'refund_value': mov.amount_total,
                        'rate': 0.00,
                        'untaxed_amt': mov.amount_untaxed,
                        'pre_gst':'N'
                    }
                    
                    cdnur.append(dict)
        
        product_list_rec = hsn_moves.invoice_line_ids.mapped('product_id')
        res = product_list_rec.ids
        for i in res:
            tax_list_rec = hsn_moves.invoice_line_ids.mapped('tax_ids')
            qty=0.00
            amt=0.00
            a=0.0
            price_total = 0.00
            price_subtot = 0.00
            kfc_amount = 0.0
            cgst_amount = 0.0
            sgst_amount = 0.0
            igst_amount = 0.0
            kfc = 0.0
            cgst = 0.0
            sgst = 0.0
            igst = 0.0
            tax_list = {}
            tax_id = False
            rate_amt = 0.00
            for mov in hsn_moves:
                
                count = 0
                for line in mov.invoice_line_ids:
                    count = count +1
                    if i==line.product_id.id:
                        qty=qty + line.quantity
                        if mov.move_type == 'out_invoice':
                            amt=amt + line.price_subtotal
                            a=a+line.price_total
                        elif mov.move_type == 'out_refund':
                            amt=amt - line.price_subtotal
                            a=a-line.price_total
                        dis=line.name
                        hsnn=line.product_id.l10n_in_hsn_code
                        tax_id=line.tax_ids
                        pd=line.product_id
                        part=line.partner_id
                        curr=line.company_currency_id
                        
                        if tax_id:
                            
                            for tax_id_rec in tax_id: 
                                if not tax_list:
                                    list_dict = {
                                        'tax_id':tax_id_rec,
                                        }
                                    tax_list[tax_id_rec.id] = list_dict
                                else:
                                    if not tax_id_rec.id in tax_list.keys():
                                        list_dict = {
                                            'tax_id':tax_id_rec,
                                            }
                                        tax_id_val = tax_id_rec.id
                                        tax_list.update({tax_id_val:list_dict})
                                 
                    else:
                        pass    
                dict = {
                'price':round(a,2),
                'hsn':hsnn,
                'dis':dis,
                'tqty':qty,
                'tamt': round(amt,2),
                'kfc':kfc,
                'cgst':cgst,
                'sgst':sgst,
                'igst':igst,
                'kfc_amount':kfc_amount,
                'cgst_amount':cgst_amount,
                'sgst_amount':sgst_amount,
                'igst_amount':igst_amount,
                'rate':amt or 0.0,

                
                }  

            tax_account = []
            for tax_key in tax_list:
                tax = tax_list[tax_key]['tax_id']
                
                if tax.amount_type == 'group':
                    tax_account.append(tax.children_tax_ids.invoice_repartition_line_ids.mapped('account_id').ids)
                elif tax.amount_type == 'percent':
                    tax_account.append(tax.invoice_repartition_line_ids.mapped('account_id').ids)
                    
            tax_account = list(set(list(itertools.chain(*tax_account))))   
            
            price_total += dict['tamt']
            for acc in tax_account:
                move_line_domain = [('move_id','in',hsn_moves.ids),('parent_state','=','posted'),('product_id','=',i),('account_id','=',acc)]
                mv_line_query = self.env['account.move.line']._where_calc(move_line_domain)
                group_by = ', '.join(['"account_move_line".tax_line_id'])
                from_clause, where_clause, where_clause_params = mv_line_query.get_sql()
                
                sql = """
                SELECT sum(balance),tax_line_id  FROM %(from)s WHERE %(where)s GROUP BY %(group_by)s
                """ % {'from': from_clause, 'where': where_clause, 'group_by':group_by}
                self.env.cr.execute(sql, where_clause_params)
                move_list = list(itertools.chain(*self.env.cr.fetchall()))
                if move_list:
                    tax = self.env['account.tax'].browse(move_list[1])
                    tax_name = tax.name
                    price_total += abs(move_list[0])
                    if 'KFC' in tax_name:
                        dict.update({'kfc': tax.amount})
                        kfc_amount += move_list[0]
                        dict.update({'kfc_amount': abs(kfc_amount)})
                    if 'CGST' in tax_name:
                        dict.update({'cgst': tax.amount})
                        cgst_amount += move_list[0]
                        dict.update({'cgst_amount': abs(cgst_amount)})
                        dict.update({'rate': amt})
                    if 'SGST' in tax_name:
                        dict.update({'sgst': tax.amount})
                        sgst_amount += move_list[0]
                        dict.update({'sgst_amount': abs(sgst_amount)})
                        dict.update({'rate': amt})
                    if 'IGST' in tax_name:
                        dict.update({'igst': tax.amount})
                        igst_amount += move_list[0]
                        dict.update({'igst_amount': abs(igst_amount)})
                        dict.update({'rate': amt})
            dict.update({'price': round(price_total,2)})
            
            
            hsn.append(dict)  
                 
               
         
        j_list=[]
                
       
        for mov in doc_moves:
            j_list.append(mov.journal_id.id)
        res = list(OrderedDict.fromkeys(j_list))   

        for i in res: 
            doc_count=0  
            cancel_count=0     
            l=[]       
            for mov in doc_moves:
                  
                if mov.journal_id.id==i:
                     
                    l.append(mov.name)
                    doc_count=doc_count+1
                    if mov.state == 'cancel':
                        cancel_count=cancel_count+1
            dict = {
                'nature':'Invoice For Outward Supply',
                'start':l[-1],
                'end':l[0],
                'total':doc_count,
                'cancel':cancel_count
                }  
                    
            doc.append(dict)  
        j_list1=[]      
        for mov in doc_moves1:
            j_list1.append(mov.journal_id.id)
        res = list(OrderedDict.fromkeys(j_list1))   
                
        for i in res: 
            doc_count=0  
            cancel_count=0     
            l=[]       
            for mov in doc_moves1:
                  
                if mov.journal_id.id==i:
                     
                    l.append(mov.name)
                    doc_count=doc_count+1
                    if mov.state == 'cancel':
                        cancel_count=cancel_count+1
            dict = {
                'nature':'Credit Note',
                'start':l[-1],
                'end':l[0],
                'total':doc_count,
                'cancel':cancel_count
                }  
                    
            doc.append(dict)          
            
            
                    
            
            
        invoice_total_sum = 0.00
        tax_total = 0.00
        sgst_total = 0.00
        igst_total = 0.00
        cgst_total = 0.00
        kfc_total = 0.00
        for res in b2b:
            row1 += 1
            worksheet1.write(row1 + 1, column, res['gst_no'], format3)
            worksheet1.write(row1 + 1, column + 1, res['receiver'], format3)
            worksheet1.write(row1 + 1, column + 2,  res['inv_no'], format3)
            worksheet1.write(row1 + 1, column + 3, res['hsn'] or '996813', format3)
            worksheet1.write(row1 + 1, column + 4,  res['inv_date'], date_format)
            worksheet1.write(row1 + 1, column + 5,  float(res['inv_value']), format_num)
            invoice_total_sum = invoice_total_sum +  res['inv_value']
            worksheet1.write(row1 + 1, column + 6,  res['place'], format3)
            worksheet1.write(row1 + 1, column + 7, 'N', format3)
            worksheet1.write(row1 + 1, column + 8,  '%.2f' % res['rate'], format_num)
            worksheet1.write(row1 + 1, column + 9,  float(res['untaxed_amt']), format_num)
            tax_total = tax_total +  res['untaxed_amt']
            if res['kfc']:
                worksheet1.write(row1 + 1, column + 10, '%.2f' % res['kfc'], format_num)
            else:
                worksheet1.write(row1 + 1, column + 10, '-', format3)
            if res['igst']:
                worksheet1.write(row1 + 1, column + 11, '%.2f' % res['igst'], format_num)
            else:
                worksheet1.write(row1 + 1, column + 11, '-', format3)
            if res['cgst']:
                worksheet1.write(row1 + 1, column + 12, '%.2f' % res['cgst'], format_num)
            else:
                worksheet1.write(row1 + 1, column + 12, '-', format3)
            if res['sgst']:
                worksheet1.write(row1 + 1, column + 13, '%.2f' % res['sgst'], format_num)
            else:
                worksheet1.write(row1 + 1, column + 13, '-', format3)
            if res['kfc_amount']:
                worksheet1.write(row1 + 1, column + 14, '%.2f' % float(res['kfc_amount']), format_num)
                kfc_total = kfc_total +  res['kfc_amount']
            else:
                worksheet1.write(row1 + 1, column + 14, '-', format3)
            if res['igst_amount']:
                worksheet1.write(row1 + 1, column + 15, '%.2f' % float(res['igst_amount']), format_num)
                igst_total = igst_total +  res['igst_amount']
            else:
                worksheet1.write(row1 + 1, column + 15, '-', format3) 
            if res['cgst_amount']:
                worksheet1.write(row1 + 1, column + 16, '%.2f' % float(res['cgst_amount']), format_num)
                cgst_total = cgst_total +  res['cgst_amount']
            else:
                worksheet1.write(row1 + 1, column + 16, '-', format3)
            if res['sgst_amount']:
                worksheet1.write(row1 + 1, column + 17, '%.2f' % float(res['sgst_amount']), format_num)
                sgst_total = sgst_total +  res['sgst_amount']
            else:
                worksheet1.write(row1 + 1, column + 17, '-', format3)  
          
        worksheet1.write(row1 + 3, column + 1,'Total', cell_text_format)
        worksheet1.write(row1 + 3, column + 5,'%.2f' % invoice_total_sum, cell_num_format)
        worksheet1.write(row1 + 3, column + 9,'%.2f' % tax_total, cell_num_format)
        worksheet1.write(row1 + 3, column + 14,'%.2f' % kfc_total, cell_num_format)
        worksheet1.write(row1 + 3, column + 15,'%.2f' % igst_total, cell_num_format)
        worksheet1.write(row1 + 3, column + 16,'%.2f' % cgst_total, cell_num_format)
        worksheet1.write(row1 + 3, column + 17,'%.2f' % sgst_total, cell_num_format)
        
        invoice_total_sum_b2c = 0.00
        tax_total_b2c = 0.00
        sgst_total_b2c = 0.00
        igst_total_b2c = 0.00
        cgst_total_b2c = 0.00
        kfc_total_b2c = 0.00
        sgst_amount_total_b2c = 0.00
        igst_amount_total_b2c = 0.00
        cgst_amount_total_b2c = 0.00
        kfc_amount_total_b2c = 0.00
        for retail in b2c:
            row2 += 1
            worksheet2.write(row2 + 1, column, '', format3)
            worksheet2.write(row2 + 1, column + 1, retail['place'], format3)
            worksheet2.write(row2 + 1, column + 2, retail['hsn'] or '996813', format3)
            worksheet2.write(row2 + 1, column + 3, float(retail['inv_value']), format_num)
            invoice_total_sum_b2c= invoice_total_sum_b2c + retail['inv_value']
            worksheet2.write(row2 + 1, column + 4, float(retail['untaxed_amt']), format_num)
            tax_total_b2c = tax_total_b2c + retail['untaxed_amt']
            if retail['kfc_amount']:
                worksheet2.write(row2 + 1, column + 5, '%.2f' % float(retail['kfc_amount']), format_num)
                kfc_amount_total_b2c = kfc_amount_total_b2c + retail['kfc_amount']
            else:
                worksheet2.write(row2 + 1, column + 5, '-', format3)
            if retail['igst_amount']:
                worksheet2.write(row2 + 1, column + 6, '%.2f' % float(retail['igst_amount']), format_num)
                igst_amount_total_b2c = igst_amount_total_b2c + retail['igst_amount']
            else:
                worksheet2.write(row2 + 1, column + 6, '-', format3)
            if retail['cgst_amount']:
                worksheet2.write(row2 + 1, column + 7, '%.2f' % float(retail['cgst_amount']), format_num)
                cgst_amount_total_b2c = cgst_amount_total_b2c + retail['cgst_amount']
            else:
                worksheet2.write(row2 + 1, column + 7, '-', format3)
            if retail['sgst_amount']:
                worksheet2.write(row2 + 1, column + 8, '%.2f' % float(retail['cgst_amount']), format_num)
                sgst_amount_total_b2c = sgst_amount_total_b2c + retail['cgst_amount']
            else:
                worksheet2.write(row2 + 1, column + 8, '-', format3)
            
        worksheet2.write(row2 + 2, column + 1,'Total', cell_text_format)
        worksheet2.write(row2 + 2, column + 3,'%.2f' % invoice_total_sum_b2c, cell_num_format)
        worksheet2.write(row2 + 2, column + 4,'%.2f' % tax_total_b2c, cell_num_format)
        worksheet2.write(row2 + 2, column + 5,'%.2f' % kfc_amount_total_b2c, cell_num_format)
        worksheet2.write(row2 + 2, column + 6,'%.2f' % igst_amount_total_b2c, cell_num_format)
        worksheet2.write(row2 + 2, column + 7,'%.2f' % cgst_amount_total_b2c, cell_num_format)
        worksheet2.write(row2 + 2, column + 8,'%.2f' % sgst_amount_total_b2c, cell_num_format)
        
        worksheet3.write(row_cdnr, column, len(set(vat_list)), cell_text_format)
        worksheet3.write(row_cdnr, column + 1, len(set(inv_list)), cell_text_format)
        worksheet3.write(row_cdnr, column + 3, len(set(refund_list)), cell_text_format)
        worksheet3.write(row_cdnr, column + 8, total_refund, cell_num_format)
        worksheet3.write(row_cdnr, column + 10, total_taxable_val, cell_num_format)
        worksheet3.write(row_cdnr, column + 11, 0.00, cell_num_format)
        
        invoice_total_sum_cdnr = 0.00
        tax_total_cdnr = 0.00
        for res in cdnr:
            row3 += 1
        
            worksheet3.write(row3 + 1, column, res['gst_no'], format3)
            worksheet3.write(row3 + 1, column + 1, res['inv_no'], format3)
            worksheet3.write(row3 + 1, column + 2, res['receiver'], format3)
            worksheet3.write(row3 + 1, column + 3,  res['inv_date'], date_format)
            worksheet3.write(row3 + 1, column + 4,  res['refund_no'], format3)
            worksheet3.write(row3 + 1, column + 5,  res['refund_date'], date_format)
            worksheet3.write(row3 + 1, column + 6,  res['doc_type'], format3)
            invoice_total_sum_cdnr = invoice_total_sum_cdnr +  res['refund_value']
            worksheet3.write(row3 + 1, column + 7,  res['reason'], format3)
            worksheet3.write(row3 + 1, column + 8,  res['place'], format3)
            worksheet3.write(row3 + 1, column + 9, float(res['refund_value']), format_num)
            worksheet3.write(row3 + 1, column + 10,  '%.2f' % res['rate'], format3)
            worksheet3.write(row3 + 1, column + 11,  float(res['untaxed_amt']), format_num)
            tax_total_cdnr = tax_total_cdnr +  res['untaxed_amt']
            worksheet3.write(row3 + 1, column + 12,0.0, format3)
            worksheet3.write(row3 + 1, column + 13,res['pre_gst'], format3)
            
        invoice_total_sum_cdnr = 0.00
        tax_total_cdnur = 0.00
        for res in cdnur:
            row4 += 1
        
            worksheet4.write(row4 + 1, column, res['ur_type'], format3)
            worksheet4.write(row4 + 1, column + 1, res['refund_no'], format3)
            worksheet4.write(row4 + 1, column + 2,  res['refund_date'], date_format)
            worksheet4.write(row4 + 1, column + 3,  res['doc_type'], format3)
            worksheet4.write(row4 + 1, column + 4,  res['inv_no'], format3)
            worksheet4.write(row4 + 1, column + 5,  res['inv_date'], date_format)
            invoice_total_sum_cdnr = invoice_total_sum_cdnr +  res['refund_value']
            worksheet4.write(row4 + 1, column + 6,  res['reason'], format3)
            worksheet4.write(row4 + 1, column + 7,  res['place'], format3)
            worksheet4.write(row4 + 1, column + 8, float(res['refund_value']), format_num)
            worksheet4.write(row4 + 1, column + 9,  '%.2f' % res['rate'], format3)
            worksheet4.write(row4 + 1, column + 10,  float(res['untaxed_amt']), format_num)
            tax_total_cdnur = tax_total_cdnur +  res['untaxed_amt']
            worksheet4.write(row4 + 1, column + 11,0.0, format3)
            worksheet4.write(row4 + 1, column + 12,res['pre_gst'], format3)    
        for res in hsn:
            row5+= 1
            worksheet5.write(row5 + 1, column, res['hsn'], format3)
            worksheet5.write(row5 + 1, column + 1, res['dis'], format3)
            worksheet5.write(row5 + 1, column + 2, '', format3)
            worksheet5.write(row5 + 1, column + 3,  res['tqty'], format3)
            worksheet5.write(row5 + 1, column + 4,  res['price'], format_num)
            worksheet5.write(row5 + 1, column + 5,  res['rate'], format_num)
            worksheet5.write(row5 + 1, column + 6,  res['igst_amount'], format_num)
            worksheet5.write(row5 + 1, column + 7,  res['cgst_amount'], format_num)
            worksheet5.write(row5 + 1, column + 8,  res['sgst_amount'], format_num)
            worksheet5.write(row5 + 1, column + 9,  0.0, format_num)
        
        for res in doc:
            row6+= 1
            worksheet6.write(row6 + 1, column, res['nature'], format3)
            worksheet6.write(row6 + 1, column + 1, res['start'], format3)
            worksheet6.write(row6 + 1, column + 2, res['end'], format3)
            worksheet6.write(row6 + 1, column + 3,  float(res['total']), format_num)
            worksheet6.write(row6 + 1, column + 4,  res['cancel'], format3)

        
        b2c_invoice_total_sum = 0.00
        b2c_tax_total = 0.00
        b2c_sgst_total = 0.00
        b2c_igst_total = 0.00
        b2c_cgst_total = 0.00
        b2c_kfc_total = 0.00
        
        for res in b2c_list:
            row7 += 1
            worksheet7.write(row7 + 1, column,  res['inv_no'], format3)
            worksheet7.write(row7 + 1, column + 1,  res['inv_date'], date_format)
            worksheet7.write(row7 + 1, column + 2,  float(res['inv_value']), format_num)
            b2c_invoice_total_sum = b2c_invoice_total_sum +  res['inv_value']
            worksheet7.write(row7 + 1, column + 3,  res['place'], format3)
            worksheet7.write(row7 + 1, column + 4,  res['hsn'], format3)
            worksheet7.write(row7 + 1, column + 5,  float(res['untaxed_amt']), format_num)
            b2c_tax_total = b2c_tax_total +  res['untaxed_amt']
            if res['kfc_amount']:
                worksheet7.write(row7 + 1, column + 6, '%.2f' % float(res['kfc_amount']), format_num)
                b2c_kfc_total = b2c_kfc_total +  res['kfc_amount']
            else:
                worksheet7.write(row7 + 1, column + 6, '-', format3)
            if res['igst_amount']:
                worksheet7.write(row7 + 1, column + 7, '%.2f' % float(res['igst_amount']), format_num)
                b2c_igst_total = b2c_igst_total +  res['igst_amount']
            else:
                worksheet7.write(row7 + 1, column + 7, '-', format3) 
            if res['cgst_amount']:
                worksheet7.write(row7 + 1, column + 8, '%.2f' % float(res['cgst_amount']), format_num)
                b2c_cgst_total = b2c_cgst_total +  res['cgst_amount']
            else:
                worksheet7.write(row7 + 1, column + 8, '-', format3)
            if res['sgst_amount']:
                worksheet7.write(row7 + 1, column + 9, '%.2f' % float(res['sgst_amount']), format_num)
                b2c_sgst_total = b2c_sgst_total +  res['sgst_amount']
            else:
                worksheet7.write(row7 + 1, column + 9, '-', format3)  
          
        worksheet7.write(row7 + 3, column ,'Total', cell_text_format)
        worksheet7.write(row7 + 3, column + 2,'%.2f' % b2c_invoice_total_sum, cell_num_format)
        worksheet7.write(row7 + 3, column + 5,'%.2f' % b2c_tax_total, cell_num_format)
        worksheet7.write(row7 + 3, column + 6,'%.2f' % b2c_kfc_total, cell_num_format)
        worksheet7.write(row7 + 3, column + 7,'%.2f' % b2c_igst_total, cell_num_format)
        worksheet7.write(row7 + 3, column + 8,'%.2f' % b2c_cgst_total, cell_num_format)
        worksheet7.write(row7 + 3, column + 9,'%.2f' % b2c_sgst_total, cell_num_format)          
            
          
        
