from odoo import models, fields
import logging
import datetime
from datetime import datetime
import pytz
import json
_logger = logging.getLogger('__name__')
import re


class SalespersonExcelReport(models.AbstractModel):
    _name = "report.account_gst_report.gstr2_report_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, obj):
        cell_text_format = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 10})
        format3 = workbook.add_format({'align': 'left', 'bold': False, 'font_size': 10})
        head = workbook.add_format({'align': 'center', 'size': 12, 'bold': True})
        head2 = workbook.add_format({'align': 'center', 'size': 10, 'bold': True})
        head3 = workbook.add_format({'align': 'center', 'font_size': 10, 'bold': True, 'bg_color': '#808080'})
        worksheet1 = workbook.add_worksheet('GSTR2 Report')
        company_name = self.env.user.company_id.name
        company_street = self.env.user.company_id.street or ''
        company_street2 = self.env.user.company_id.street2 or ''
        company_city = self.env.user.company_id.city or ''
        company_zip = self.env.user.company_id.zip or ''
        company_addr = str(company_street + ' , ' + ' ' + company_street2 + '  ' + company_city + '  ' + company_zip)
        company_mob = self.env.user.company_id.phone or ''
        company_email = self.env.user.company_id.email or ''
        company_website = self.env.user.company_id.website or ''
        if company_mob and company_email and company_website:
            company_addr1 = 'Ph:' + company_mob + ',' + ' ' + 'Email:' + company_email + ',' + ' ' + 'Website:' + company_website
        else:
            company_addr1 = ''
        worksheet1.set_column('A:A', 18)
        worksheet1.set_column('B:B', 25)
        worksheet1.set_column('C:C', 16)
        worksheet1.set_column('D:D', 16)
        worksheet1.set_column('E:E', 12)
        worksheet1.set_column('F:F', 15)
        worksheet1.set_column('G:G', 15)
        worksheet1.set_column('H:H', 15)
        worksheet1.set_column('I:I', 8)
        worksheet1.set_column('J:J', 12)
        worksheet1.set_column('K:K', 8)
        worksheet1.set_column('L:L', 8)
        worksheet1.set_column('M:M', 8)

        worksheet1.merge_range('A1:F2', company_name, head)
        worksheet1.merge_range('A3:F4', company_addr, head2)
        worksheet1.merge_range('A5:F6', company_addr1, head2)

        row = 7
        column = 0

        worksheet1.merge_range('B7:E7', 'GST Report', head)
        row += 2

        from_date = fields.Date.from_string(data['from_date']).strftime('%d/%m/%Y')
        to_date = fields.Date.from_string(data['to_date']).strftime('%d/%m/%Y')

        worksheet1.write(row, column, 'From Date', cell_text_format)
        worksheet1.write(row, column + 1, from_date, cell_text_format)
        worksheet1.write(row, column + 3, 'To Date', cell_text_format)
        worksheet1.write(row, column + 4, to_date, cell_text_format)

        row += 2
        worksheet1.write(row, column, 'GSTIN/UIN of Recipient', cell_text_format)
        worksheet1.write(row, column + 1, 'Receiver Name', cell_text_format)
        worksheet1.write(row, column + 2, 'Invoice Number', cell_text_format)
        worksheet1.write(row, column + 3, 'Reference Number', cell_text_format)
        worksheet1.write(row, column + 4, 'HSN code', cell_text_format)
        worksheet1.write(row, column + 5, 'Invoice Date', cell_text_format)
        worksheet1.write(row, column + 6, 'Invoice Value', cell_text_format)
        worksheet1.write(row, column + 7, 'Place of supply', cell_text_format)
        worksheet1.write(row, column + 8, 'Reverse Charge', cell_text_format)
        worksheet1.write(row, column + 9, 'Rate', cell_text_format)
        worksheet1.write(row, column + 10, 'Taxable value', cell_text_format)
        worksheet1.write(row, column + 11, 'KFC %', cell_text_format)
        worksheet1.write(row, column + 12, 'IGST', cell_text_format)
        worksheet1.write(row, column + 13, 'CGST', cell_text_format)
        worksheet1.write(row, column + 14, 'SGST', cell_text_format)
        worksheet1.write(row, column + 15, 'KFC Amount', cell_text_format)
        worksheet1.write(row, column + 16, 'IGST Amount', cell_text_format)
        worksheet1.write(row, column + 17, 'CGST Amount', cell_text_format)
        worksheet1.write(row, column + 18, 'SGST Amount', cell_text_format)

        inv_list = []
        domain = [('move_type', '=', 'in_invoice'), ('state', '=', 'posted')]
        service_type = self.env['partner.service.type'].search([('id', '=', data['service_type'][0])])

        if data['from_date']:
            domain.append(('invoice_date', '>=', data['from_date']))
        if data['to_date']:
            domain.append(('invoice_date', '<=', data['to_date']))
        if data['state_ids']:
            domain.append(('partner_id.state_id.id', 'in', data['state_ids']))   
            
        if data['service_type']:
            if service_type.is_fleet_service or service_type.is_qshop_service:
                domain.append(('service_type_id','=',service_type.id))
            else:
                domain.append(('service_type_id','in',[service_type.id, False]))


               
        moves = self.env['account.move'].search(domain)
        for mov in moves:
            if mov.partner_id.vat:
                for line in mov.invoice_line_ids:
                    taxes = line.tax_ids._origin.compute_all(
                        line.price_subtotal,
                        currency=line.company_currency_id,
                        quantity=line.quantity,
                        product=line.product_id,
                        partner=line.partner_id,
                    )
                    dict = {
                        'gst_no': mov.partner_id.vat,
                        'receiver': mov.partner_id.name,
                        'inv_no': mov.name,
                        'ref_no': mov.ref,
                        'place': mov.partner_id.state_id.name,
                        'inv_date': mov.invoice_date.strftime('%d/%m/%Y'),
                        'inv_value': mov.amount_total,
                        'cgst': 0.00,
                        'sgst': 0.00,
                        'igst': 0.00,
                        'kfc': 0.00,
                        'rate': 0.00,
                        'igst_amount':0.00,
                        'cgst_amount':0.00,
                        'sgst_amount':0.00,
                        'kfc_amount':0.00,
                        'untaxed_amt': mov.amount_untaxed,
                    }
                    inv_list.append(dict)
                    for i in taxes['taxes']:
                        tax_name = i['name']
                        tax = self.env['account.tax'].browse(i['id'])
                        if 'KFC' in tax_name:
                            dict.update({'kfc': tax.amount})
                            dict.update({'kfc_amount': (1/100)*mov.amount_untaxed})
                            dict.update({'rate': dict['rate'] + tax.amount})                      
                        if 'CGST' in tax_name:
                            dict.update({'cgst': tax.amount})
                            dict.update({'cgst_amount': (tax.amount/100)*mov.amount_untaxed})
                            dict.update({'rate': dict['rate'] + tax.amount})
                        if 'SGST' in tax_name:
                            dict.update({'sgst':tax.amount})
                            dict.update({'sgst_amount': (tax.amount/100)*mov.amount_untaxed})
                            dict.update({'rate': dict['rate'] + tax.amount})
                        if 'IGST' in tax_name:
                            dict.update({'igst': tax.amount})
                            dict.update({'igst_amount': (tax.amount/100)*mov.amount_untaxed})
                            dict.update({'rate': dict['rate'] + tax.amount})
        invoice_total_sum = 0.00
        tax_total = 0.00
        sgst_total = 0.00
        igst_total = 0.00
        cgst_total = 0.00
        kfc_total = 0.00                    

        for res in inv_list:
            row += 1
            worksheet1.write(row + 1, column, res['gst_no'], format3)
            worksheet1.write(row + 1, column + 1, res['receiver'], format3)
            worksheet1.write(row + 1, column + 2,  res['inv_no'], format3)
            worksheet1.write(row + 1, column + 3,  res['ref_no'], format3)
            worksheet1.write(row + 1, column + 4,'996813', format3)
            worksheet1.write(row + 1, column + 5,  res['inv_date'], format3)
            worksheet1.write(row + 1, column + 6,  res['inv_value'], format3)
            invoice_total_sum = invoice_total_sum +  res['inv_value']
            worksheet1.write(row + 1, column + 7,  res['place'], format3)
            worksheet1.write(row + 1, column + 8, 'N', format3)
            worksheet1.write(row + 1, column + 9,  '%.2f' % res['rate'], format3)
            worksheet1.write(row + 1, column + 10,  res['untaxed_amt'], format3)
            tax_total = tax_total +  res['untaxed_amt']
            if res['kfc']:
                worksheet1.write(row + 1, column + 11, '%.2f' % res['kfc'], format3)
            else:
                worksheet1.write(row + 1, column + 11, '-', format3)
            if res['igst']:
                worksheet1.write(row + 1, column + 12, '%.2f' % res['igst'], format3)
            else:
                worksheet1.write(row + 1, column + 12, '-', format3)
            if res['cgst']:
                worksheet1.write(row + 1, column + 13, '%.2f' % res['cgst'], format3)
            else:
                worksheet1.write(row + 1, column + 13, '-', format3)
            if res['sgst']:
                worksheet1.write(row + 1, column + 14, '%.2f' % res['sgst'], format3)
            else:
                worksheet1.write(row + 1, column + 14, '-', format3)
            if res['kfc_amount']:
                worksheet1.write(row + 1, column + 15, '%.2f' % res['kfc_amount'], format3)
                kfc_total = kfc_total +  res['kfc_amount']
            else:
                worksheet1.write(row + 1, column + 15, '-', format3)
            if res['igst_amount']:
                worksheet1.write(row + 1, column + 16, '%.2f' % res['igst_amount'], format3)
                igst_total = igst_total +  res['igst_amount']
            else:
                worksheet1.write(row + 1, column + 16, '-', format3) 
            if res['cgst_amount']:
                worksheet1.write(row + 1, column + 17, '%.2f' % res['cgst_amount'], format3)
                cgst_total = cgst_total +  res['cgst_amount']
            else:
                worksheet1.write(row + 1, column + 17, '-', format3)
            if res['sgst_amount']:
                worksheet1.write(row + 1, column + 18, '%.2f' % res['sgst_amount'], format3)
                sgst_total = sgst_total +  res['sgst_amount']
            else:
                worksheet1.write(row + 1, column + 18, '-', format3)
        worksheet1.write(row + 3, column + 1,'Total', cell_text_format)
        worksheet1.write(row + 3, column + 6,'%.2f' % invoice_total_sum, cell_text_format)
        worksheet1.write(row + 3, column + 10,'%.2f' % tax_total, cell_text_format)
        worksheet1.write(row + 3, column + 15,'%.2f' % kfc_total, cell_text_format)
        worksheet1.write(row + 3, column + 16,'%.2f' % igst_total, cell_text_format)
        worksheet1.write(row + 3, column + 17,'%.2f' % cgst_total, cell_text_format)
        worksheet1.write(row + 3, column + 18,'%.2f' % sgst_total, cell_text_format)        

