# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from operator import itemgetter
from odoo.tools import float_is_zero


class TdsReport(models.AbstractModel):
    _name = 'report.account_base.tds_report_export.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def get_report_datas(self, active_model):
        account_tax_id_list = self.env['account.tax'].search([('is_tds', '=', True)])
        if active_model.account_tax_ids:
            account_tax_id_list = active_model.account_tax_ids
        payment_type = "outbound" if active_model.type == "in_invoice" else "inbound"
        domain = ['|', ('move_id.move_type', '=', active_model.type),
                  ('payment_id.payment_type', '=', payment_type),
                  ('move_id.state', '=', 'posted'),
                  ('move_id.date', '>=', active_model.from_date), ('move_id.date', '<=', active_model.to_date),
                  ('move_id.company_id', '=', active_model.company_id.id),
                  ('tax_ids', 'in', account_tax_id_list.ids)]
        line_data = self.env['account.move.line'].search(domain)
        dict = {}
        section_dict = defaultdict()
        for line in line_data:
            # if line.id not in dict:
            invoice_date = line.move_id.invoice_date or  ""
            date = line.move_id.date or ""
            name = line.move_id.name or ""
            if line.move_id.move_type == 'out_invoice':
                type = "Customer Invoice"
            elif line.move_type == 'in_invoice':
                type = "Vendor Bill"
            elif line.payment_id.payment_type == "outbound":
                type = "Advance Payment"
            else:
                type = ""
            company_status = ''
            tds_rate = ''
            tax_name = ''
            tax_group = 0
            for tds_tax in line.tax_ids:
                if tds_tax.tds_applicable:
                    company_status += tds_tax.tds_applicable + ' ' + '/'
                if tds_tax.amount:
                    tds_rate += str(tds_tax.amount) + ' ' + '/'
                if tds_tax.name:
                    tax_name += tds_tax.name + ' ' + '/'
                if tds_tax.tax_group_id:
                    tax_group = tds_tax.tax_group_id.id
                if company_status:
                    company_stat = company_status
                else:
                    company_stat = ''

                if line.partner_id:
                    vendor_name = line.partner_id.name
                else:
                    vendor_name = ''
                if line.ref:
                    reference = line.ref
                else:
                    reference = ''
                if line.partner_id.l10n_in_pan:
                    pan_no = line.partner_id.l10n_in_pan
                else:
                    pan_no = ''
                if line.amount_currency:
                    amount_untaxed = line.amount_currency
                else:
                    amount_untaxed = 0.00
                if tax_name:
                    section = tax_name
                else:
                    section = ''
                if tds_rate:
                    tds_tax_rate = tds_rate
                else:
                    tds_tax_rate = ''
                amount = False
                if line.move_id.tax_totals:
                    untaxed_amount = line.move_id.tax_totals['groups_by_subtotal']['Untaxed Amount']
                    filtered_data = [item for item in untaxed_amount if item['tax_group_id'] == tax_group]

                    for rec in filtered_data:
                        amount += rec['tax_group_amount']
                elif line.payment_id.tax_tds_id:
                    untaxed_amount = line.payment_id.amount_total
                    amount = line.payment_id.amount_total - line.payment_id.amount
                if amount:
                    tds_amount = amount
                else:
                    tds_amount = 0
                if tds_amount:
                    if tds_tax.id in section_dict:
                        section_dict[tds_tax.id].update({line.id: {'invoice_date': invoice_date, 'date': date,
                                                          'name': name,
                                                          'type': type,
                                                          'status_company': company_stat,
                                                          'vendor_name': vendor_name,
                                                          'reference': reference,
                                                          'pan_no': pan_no,
                                                          'amount_untaxed': amount_untaxed,
                                                          'section': section,
                                                          'tds_rate': tds_tax_rate,
                                                          'tds_amount': tds_amount
                                                          }})
                    else:
                        section_dict[tds_tax.id] = {line.id: {'invoice_date': invoice_date, 'date': date,
                                                                   'name': name,
                                                                   'type': type,
                                                                   'status_company': company_stat,
                                                                   'vendor_name': vendor_name,
                                                                   'reference': reference,
                                                                   'pan_no': pan_no,
                                                                   'amount_untaxed': amount_untaxed,
                                                                   'section': section,
                                                                   'tds_rate': tds_tax_rate,
                                                                   'tds_amount': tds_amount
                                                                   }}

        return section_dict

    def generate_xlsx_report(self, workbook, data, active_model):
        # FORMATS STARTS
        design_formats = {'heading_format': workbook.add_format({'align': 'center',
                                                                 'valign': 'vjustify',
                                                                 'bold': True, 'size': 13,
                                                                 'font_name': 'Times New Roman',
                                                                 'text_wrap': True, 'shrink': True}),
                          'heading_format_1': workbook.add_format({'align': 'left',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   'text_wrap': True, 'shrink': True}),
                          'heading_format_2': workbook.add_format({'align': 'left',
                                                                   'valign': 'vjustify',
                                                                   'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   'text_wrap': True, 'shrink': True}),
                          'heading_format_3': workbook.add_format({'align': 'center',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   'text_wrap': True, 'shrink': True}),
                          'sub_heading_format': workbook.add_format({'align': 'right',
                                                                     'valign': 'vjustify',
                                                                     'bold': True, 'size': 9,
                                                                     'font_name': 'Times New Roman',
                                                                     'text_wrap': True, 'shrink': True}),
                          'sub_heading_format_left': workbook.add_format({'align': 'left',
                                                                          'valign': 'vjustify',
                                                                          'bold': True, 'size': 9,
                                                                          'font_name': 'Times New Roman',
                                                                          'text_wrap': True, 'shrink': True}),
                          'sub_heading_format_center': workbook.add_format({'align': 'center',
                                                                            'valign': 'vjustify',
                                                                            'bold': True, 'size': 9,
                                                                            'font_name': 'Times New Roman',
                                                                            'text_wrap': True, 'shrink': True}),
                          'bold': workbook.add_format({'bold': True, 'font_name': 'Times New Roman',
                                                       'size': 12,
                                                       'text_wrap': True}),
                          'bold2': workbook.add_format({'bold': True, 'font_name': 'Times New Roman',
                                                        'size': 11,
                                                        'text_wrap': True}),
                          'bold_center': workbook.add_format({'bold': True, 'font_name': 'Times New Roman',
                                                              'size': 11,
                                                              'text_wrap': True,
                                                              'align': 'center'}),
                          'date_format': workbook.add_format({'num_format': 'dd/mm/yyyy',
                                                              'font_name': 'Times New Roman', 'size': 11,
                                                              'align': 'left', 'text_wrap': True}),
                          'datetime_format': workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm:ss',
                                                                  'font_name': 'Times New Roman', 'size': 11,
                                                                  'align': 'center', 'text_wrap': True}),
                          'normal_format': workbook.add_format({'font_name': 'Times New Roman',
                                                                'size': 11, 'align': 'left', 'text_wrap': True}),
                          'normal_format_right': workbook.add_format({'font_name': 'Times New Roman',
                                                                      'align': 'right', 'size': 11,
                                                                      'text_wrap': True}),
                          'normal_format_right_bold': workbook.add_format({'font_name': 'Times New Roman',
                                                                           'align': 'right', 'size': 11,
                                                                           'text_wrap': True, 'bold': True}),
                          'normal_format_central': workbook.add_format({'font_name': 'Times New Roman',
                                                                        'size': 11, 'align': 'center',
                                                                        'text_wrap': True}),
                          'amount_format': workbook.add_format({'num_format': '#,##0.00',
                                                                'font_name': 'Times New Roman',
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
                                                                    'align': 'right', 'size': 11,
                                                                    'text_wrap': True}),
                          'float_number_total': workbook.add_format({
                              'bold': True,
                              'size': 11,
                              'align': 'right',
                              'text_wrap': True,
                              'font_name': 'Times New Roman',
                          }),
                          'int_rate_format': workbook.add_format({'num_format': '###0',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True})}
        # FORMATS END
        worksheet = workbook.add_worksheet("TDS Report")
        from_date = active_model.from_date.strftime('%d/%m/%Y')
        to_date = active_model.to_date.strftime('%d/%m/%Y')
        type = active_model.type
        if active_model.sections:
            sections = active_model.sections
        else:
            sections = ""
        company = active_model.company_id.name

        company_id = active_model.company_id
        company_street = company_id.street if company_id.street else ''
        company_street2 = company_id.street2 if company_id.street2 else ''
        company_city = company_id.city if company_id.city else ''
        company_zip = company_id.zip if company_id.zip else ''
        company_addr = str(company_street + ' , ' + ' ' + company_street2 + '  ' + company_city + '  ' + company_zip)
        company_mob = company_id.phone if company_id.phone else ''
        company_email = company_id.email if company_id.email else ''
        company_website = company_id.website if company_id.website else ''
        if company_mob and company_email and company_website:
            company_addr1 = 'Ph:' + company_mob + ',' + ' ' + 'Email:' + company_email + ',' + ' ' + 'Website:' + company_website
        else:
            company_addr1 = ''

        today = fields.Date.today()
        user_id = self.env['res.users'].browse(self.env.uid)
        user = user_id.name
        account_lines = self.get_report_datas(active_model)

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 30)
        worksheet.set_column('F:F', 30)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 20)
        worksheet.set_column('J:J', 20)
        worksheet.set_column('K:K', 20)
        worksheet.set_column('L:L', 20)

        worksheet.merge_range('A1:G2', company, design_formats['heading_format'])
        worksheet.merge_range('A3:G4', company_addr, design_formats['heading_format_3'])
        worksheet.merge_range('A5:G6', company_addr1, design_formats['heading_format_3'])
        worksheet.write(6, 3, "Printed Date", design_formats['heading_format_1'])
        worksheet.write(6, 4, today, design_formats['date_format'])
        worksheet.write(7, 3, "Printed User", design_formats['heading_format_1'])
        worksheet.write(7, 4, user, design_formats['heading_format_2'])
        worksheet.write(8, 3, "From Date", design_formats['heading_format_1'])
        worksheet.write(8, 4, from_date, design_formats['date_format'])
        worksheet.write(9, 3, "To Date", design_formats['heading_format_1'])
        worksheet.write(9, 4, to_date, design_formats['date_format'])
        worksheet.write(10, 3, "Section", design_formats['heading_format_1'])
        worksheet.write(10, 4, sections, design_formats['heading_format_2'])
        worksheet.write(12, 3, "TDS Report", design_formats['heading_format_3'])

        row = 14
        col = 0
        worksheet.write(row, col, "Invoice/Bill Date", design_formats['bold'])
        worksheet.write(row, col + 1, "Date", design_formats['bold'])
        worksheet.write(row, col + 2, "Number", design_formats['bold'])
        worksheet.write(row, col + 3, "Type", design_formats['bold'])
        worksheet.write(row, col + 4, "Status - Company/ Non Company", design_formats['bold'])
        worksheet.write(row, col + 5, "Vendor Name", design_formats['bold'])
        worksheet.write(row, col + 6, "Reference", design_formats['bold'])
        worksheet.write(row, col + 7, "PAN Number", design_formats['bold'])
        worksheet.write(row, col + 8, "TDS Applicable Amount", design_formats['bold'])
        worksheet.write(row, col + 9, "Section", design_formats['bold'])
        worksheet.write(row, col + 10, "TDS Rate", design_formats['bold'])
        worksheet.write(row, col + 11, "TDS Amount", design_formats['bold'])
        row += 1

        tds_untax_amount_grand_total = 0.00
        tds_amt_sum_grand_total = 0.00

        for line in account_lines:
            amount_untaxed_sum = 0.00
            roundoff_sum = 0.00
            net_amount_paid_sum = 0.00
            total_gross_sum = 0.00
            amount_total_sum = 0.00
            tds_untax_amount_sum = 0.00
            tds_amt_sum = 0.00
            col = 0
            if account_lines[line]:
                tax_data = self.env['account.tax'].browse(line)
                tax_name = tax_data.name
                worksheet.write(row, col, tax_name, design_formats['bold2'])
                row += 1
                for account_line in account_lines[line]:
                    col = 0
                    worksheet.write(row, col, account_lines[line][account_line]['invoice_date'],
                                    design_formats['date_format'])
                    col += 1
                    worksheet.write(row, col, account_lines[line][account_line]['date'], design_formats['date_format'])
                    col += 1
                    worksheet.write(row, col, account_lines[line][account_line]['name'],
                                    design_formats['normal_format'])
                    col += 1
                    worksheet.write(row, col, account_lines[line][account_line]['type'],
                                    design_formats['normal_format'])
                    col += 1
                    worksheet.write(row, col, account_lines[line][account_line]['status_company'],
                                    design_formats['normal_format'])
                    col += 1
                    worksheet.write(row, col, account_lines[line][account_line]['vendor_name'],
                                    design_formats['normal_format'])
                    col += 1
                    worksheet.write(row, col, account_lines[line][account_line]['reference'],
                                    design_formats['normal_format'])
                    col += 1
                    worksheet.write(row, col, account_lines[line][account_line]['pan_no'],
                                    design_formats['normal_format'])
                    col += 1
                    tds_untax_amount_sum += float(account_lines[line][account_line]['amount_untaxed'])
                    tds_untax_amount = '%.2f' % float(account_lines[line][account_line]['amount_untaxed'])
                    worksheet.write(row, col, tds_untax_amount, design_formats['normal_format_right'])
                    col += 1
                    worksheet.write(row, col, account_lines[line][account_line]['section'],
                                    design_formats['normal_format'])
                    col += 1
                    worksheet.write(row, col, account_lines[line][account_line]['tds_rate'],
                                    design_formats['normal_format'])
                    col += 1
                    tds_amt_sum += float(abs(account_lines[line][account_line]['tds_amount']))
                    tds_amt = '%.2f' % float(abs(account_lines[line][account_line]['tds_amount']))
                    worksheet.write(row, col, tds_amt, design_formats['normal_format_right'])
                    col += 1
                    row += 1
                tds_untax_amount_grand_total += tds_untax_amount_sum
                tds_untax_amount_sum = '%.2f' % float(tds_untax_amount_sum)
                worksheet.write(row, 8, tds_untax_amount_sum, design_formats['float_number_total'])
                tds_amt_sum_grand_total += tds_amt_sum
                tds_amt_sum = '%.2f' % float(tds_amt_sum)
                worksheet.write(row, 11, tds_amt_sum, design_formats['float_number_total'])

                row += 1
        worksheet.write(row, 0, "Grand Total", design_formats['float_number_total'])
        tds_untax_amount_grand_total = '%.2f' % float(tds_untax_amount_grand_total)
        worksheet.write(row, 8, tds_untax_amount_grand_total, design_formats['float_number_total'])
        tds_amt_sum_grand_total = '%.2f' % float(tds_amt_sum_grand_total)
        worksheet.write(row, 11, tds_amt_sum_grand_total, design_formats['float_number_total'])

        row += 1
