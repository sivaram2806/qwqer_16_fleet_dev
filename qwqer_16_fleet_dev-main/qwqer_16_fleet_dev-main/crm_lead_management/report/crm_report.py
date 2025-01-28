import xlsxwriter

from odoo import fields, models, api, _
import string
import logging
from io import BytesIO
import base64

_logger = logging.getLogger(__name__)

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class CrmReportXlsx(models.AbstractModel):
    _name = 'report.crm_lead_management.crm_lead_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def write_headers(self, worksheet, design_formats, headers):
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, design_formats['heading_format_2'])

    # def get_row_range(self, headers):
    #     row_range = {}
    #     row_range.update({'service_row_data': 'E2:E1048576', 'region_row_data': 'F2:F1048576','source_row_data': 'G2:G1048576',
    #                       'customer_type_row_data': 'H2:H1048576', 'customer_segment_row_data': 'I2:I1048576',
    #                       'follow_up_status_row_data': 'J2:J1048576'})
    #     return row_range

    def generate_xlsx_report(self, workbook, data, active_model):
        row_range = {'lead_name': 'A2:A1048576', 'contact_name': 'B2:B1048576', 'phone_no': 'C2:C1048576',
                     'email': 'D2:D1048576', 'service_row_data': 'E2:E1048576', 'region_row_data': 'F2:F1048576',
                     'source_row_data': 'G2:G1048576', 'customer_type_row_data': 'H2:H1048576',
                     'customer_segment_row_data': 'I2:I1048576', 'follow_up_status_row_data': 'J2:J1048576', 'sales_person_row_data': 'K2:K1048576', 'customer_industry_row_data': 'L2:L1048576'}
        design_formats = {'heading_format': workbook.add_format({'align': 'center',
                                                                 'valign': 'vcenter',
                                                                 'bold': True, 'size': 11,
                                                                 'font_name': 'Times New Roman',
                                                                 'border': True,
                                                                 'text_wrap': True, 'shrink': True}),
                          'heading_format_1': workbook.add_format({'align': 'left',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   'bg_color': 'AFE1AF', 'color': 'black',
                                                                   'border': True,
                                                                   'text_wrap': True, 'shrink': True}),
                          'heading_format_2': workbook.add_format({'align': 'center',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   'bg_color': 'AFE1AF', 'color': 'black',
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
                          'float_rate_format': workbook.add_format({'num_format': '###0.00',
                                                                    'font_name': 'Times New Roman',
                                                                    'align': 'center', 'size': 11,
                                                                    'text_wrap': True}),
                          'int_rate_format': workbook.add_format({'num_format': '###0',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True})}
        # FORMATS END
        worksheet = workbook.add_worksheet("Crm Bulk Import")
        # Drop down field in xlsx sheet that displays all service types available in system
        # fetch all service type data
        active_id = data['context'].get('active_id')
        bulk_record =self.env['crm.bulk.import'].browse(active_id)
        company_id = bulk_record.company_id.id or self.env.company.id
        service_types = self.env['partner.service.type'].search([('company_id', '=', company_id),
                                                                 ('is_customer', '=', True)])
        service_data = [(service.name or '') for service in service_types]

        # fetch all region master data

        regions = self.env['sales.region'].search([('company_id', '=', company_id)])
        region_data = [(region.name or '') for region in regions]

        sources = self.env['utm.source'].search([])
        source_data = [(source.name or '') for source in sources]

        # customer_type = self.env['crm.lead'].fields_get(allfields=['customer_type'])
        # customer_types = customer_type.get("customer_type", {}).get("selection")
        # Extract the selection values
        customer_type_data = ['B2B']

        # Drop down field in xlsx sheet that displays all customer segment available in system

        segments = self.env['partner.segment'].search([('company_id', '=', company_id),('is_customer', '=', True)])
        segment_data = [(segment.name or '') for segment in segments]

        # Drop down field in xlsx sheet that displays all followup status available in system

        follow_up_status = self.env['mail.activity.type'].search([('res_model', '=', 'crm.lead'), ('company_id', '=', company_id)])
        follow_up_data = [(fus.name or '') for fus in follow_up_status]

        # Drop down field in xlsx sheet that displays all sales person available in system

        sales_person = self.env['hr.employee'].search([('company_id', '=', company_id),('driver_uid','=',False),('user_id','!=',False)])
        sales_person_data = [(sales.user_id.name or '') for sales in sales_person]

        # Drop down field in xlsx sheet that displays all customer industry available in system

        customer_industry = self.env['res.partner.industry'].search([])
        customer_industry_data = [(industry.name or '') for industry in customer_industry]



        # Common column settings
        column_settings = string.ascii_uppercase[:16] if not self._context.get('download_template',
                                                                               False) else string.ascii_uppercase[:14]
        for i in column_settings:
            worksheet.set_column(f'{i}:{i}', 27)
        headers = [
            'Lead', 'Contact Name', 'Phone', 'Email',
            'Service Type', 'Region','Source/ Lead Type', 'Customer Type', 'Customer Segment', 'Follow Up Status','Sales Person','Customer Industry',
            'Comments'
        ]
        hidden_sheet = workbook.add_worksheet("MasterList")
        hidden_sheet.hide()
        service_type_row = 0
        for rec in service_data:
            hidden_sheet.write(service_type_row, 0, rec or '', design_formats['normal_format'])
            service_type_row += 1

        region_row = 0
        for rec in region_data:
            hidden_sheet.write(region_row, 1, rec or '', design_formats['normal_format'])
            region_row += 1

        source_row = 0
        for rec in source_data:
            hidden_sheet.write(source_row, 2, rec or '', design_formats['normal_format'])
            source_row += 1

        customer_type_row = 0
        for rec in customer_type_data:
            hidden_sheet.write(customer_type_row, 3, rec or '', design_formats['normal_format'])
            customer_type_row += 1

        segment_row = 0
        for rec in segment_data:
            hidden_sheet.write(segment_row, 4, rec or '', design_formats['normal_format'])
            segment_row += 1

        follow_up_row = 0
        for rec in follow_up_data:
            hidden_sheet.write(follow_up_row, 5, rec or '', design_formats['normal_format'])
            follow_up_row += 1

        sales_person_row = 0
        for rec in sales_person_data:
            hidden_sheet.write(sales_person_row, 6, rec or '', design_formats['normal_format'])
            sales_person_row += 1

        customer_indus_row = 0
        for rec in customer_industry_data:
            hidden_sheet.write(customer_indus_row, 7, rec or '', design_formats['normal_format'])
            customer_indus_row += 1

        # Header titles based on the context
        if self._context.get('download_template', False):
            worksheet.set_row(0, 50)
            self.write_headers(worksheet, design_formats, headers)

        elif self._context.get('download_import_failed_records', False):
            active_id = int(data.get('context').get('active_id'))
            active_model = self.env[data.get('context').get('active_model')].browse(active_id)
            for rec in active_model:
                original_file_data = base64.b64decode(rec.upload_file)
                # Open the original Excel file using xlrd
                workbook = xlrd.open_workbook(file_contents=original_file_data)
                sheet = workbook.sheet_by_index(0)
                self.write_headers(worksheet, design_formats, sheet.row_values(0))
                failed_rows = [line.row_no for line in rec.bulk_import_line_ids if line.state == 'fail']
                for idx, row_num in enumerate(failed_rows):
                    for col_index in range(sheet.ncols):
                        worksheet.write(idx + 1, col_index, sheet.cell_value(row_num, col_index))

        else:
            worksheet.set_row(0, 50)
            self.write_headers(worksheet, design_formats, headers)
            row = 1
            for rec in active_model:
                worksheet.write(row, 0, rec.name or '', design_formats['normal_format'])
                worksheet.write(row, 1, rec.contact_name or '', design_formats['normal_format'])
                worksheet.write(row, 2, rec.phone or '', design_formats['normal_format'])
                worksheet.write(row, 3, rec.email_from or '', design_formats['normal_format'])
                worksheet.write(row, 4, rec.customer_service_type.name or '', design_formats['normal_format'])
                worksheet.write(row, 5, rec.region_id.name or '', design_formats['normal_format'])
                worksheet.write(row, 6, rec.source_id.name or '', design_formats['normal_format'])
                worksheet.write(row, 7, rec.customer_type or '', design_formats['normal_format'])
                worksheet.write(row, 8, rec.customer_segment_id.name or '', design_formats['normal_format'])
                worksheet.write(row, 9, rec.followup_status_id.name or '', design_formats['normal_format'])
                worksheet.write(row, 10, rec.sales_person.name or '', design_formats['normal_format'])
                worksheet.write(row, 11, rec.customer_industry.name or '', design_formats['normal_format'])
                worksheet.write(row, 12, rec.comments or '', design_formats['normal_format'])
                row += 1

        if row_range:
            validation_data = {'service_type_row': {'row_range': row_range['service_row_data'],
                                                    'source': f"=MasterList!$A$1:$A${len(service_data)}",
                                                    'error_message': 'Please select a service type from the list.'},
                               'region_row': {'row_range': row_range['region_row_data'],
                                              'source': f"=MasterList!$B$1:$B${len(region_data)}",
                                              'error_message': 'Please select a region from the list.'},
                               'source_row': {'row_range': row_range['source_row_data'],
                                              'source': f"=MasterList!$C$1:$C${len(source_data)}",
                                              'error_message': 'Please select a source / ead type from the list.'},
                               'customer_type_row': {'row_range': row_range['customer_type_row_data'],
                                                     'source': f"=MasterList!$D$1:$D${len(customer_type_data)}",
                                                     'error_message': 'Please select a customer type from the list.'},
                               'customer_segment_row': {'row_range': row_range['customer_segment_row_data'],
                                                        'source': f"=MasterList!$E$1:$E${len(segment_data)}",
                                                        'error_message': 'Please select a customer segment from the list.'},
                               'follow_up_status_row': {'row_range': row_range['follow_up_status_row_data'],
                                                        'source': f"=MasterList!$F$1:$F${len(follow_up_data)}",
                                                        'error_message': 'Please select a follow up status from the list.'},
                               'sales_person_row': {'row_range': row_range['sales_person_row_data'],
                                                        'source': f"=MasterList!$G$1:$G${len(sales_person_data)}",
                                                        'error_message': 'Please select a Sales Person from the list.'},
                               'customer_industry_row': {'row_range': row_range['customer_industry_row_data'],
                                                        'source': f"=MasterList!$H$1:$H${len(customer_industry_data)}",
                                                        'error_message': 'Please select a Customer Industry from the list.'}

                               }

            for key, val in validation_data.items():
                worksheet.data_validation(val['row_range'], {'validate': 'list',
                                                             'source': val['source'],
                                                             'error_title': 'Invalid input',
                                                             'error_message': val['error_message']})