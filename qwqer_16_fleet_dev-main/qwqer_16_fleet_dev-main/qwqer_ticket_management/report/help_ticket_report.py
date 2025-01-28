from odoo import fields, models, api, _
import string
import logging
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


class HelpdeskTicketXlsx(models.AbstractModel):
    _name = 'report.qwqer_ticket_management.report_helpdesk_ticket_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def write_headers(self, worksheet, design_formats, headers):
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, design_formats['heading_format_2'])

    def get_row_range(self, headers):
        row_range = {}
        if 'Enquiry Number' in headers:
            row_range.update({'customer_name_row_range': 'C2:C1048576',
                              'enquiry_generated_row_range': 'D2:D1048576',
                              'vehicles_types_row_range': 'E2:E1048576',
                              'source_row_range': 'F2:F1048576',
                              'destination_row_range': 'G2:G1048576',
                              'rate_type_row_range': 'L2:L1048576',
                              'rate_given_by_row_range': 'M2:M1048576',
                              'assigned_user_row_range': 'N2:N1048576',
                              'region_row_range': 'O2:O1048576',
                              'stage_row_range': 'R2:R1048576'})
        else:
            row_range.update({'customer_name_row_range': 'B2:B1048576',
                              'enquiry_generated_row_range': 'C2:C1048576',
                              'vehicles_types_row_range': 'D2:D1048576',
                              'source_row_range': 'E2:E1048576',
                              'destination_row_range': 'F2:F1048576',
                              'rate_type_row_range': 'K2:K1048576',
                              'rate_given_by_row_range': 'L2:L1048576',
                              'assigned_user_row_range': 'M2:M1048576',
                              'region_row_range': 'N2:N1048576',})
        return row_range

    def generate_xlsx_report(self, workbook, data, active_model):
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
        worksheet = workbook.add_worksheet("Fleet Enquiry Bulk Import")

        city_data = self.env['res.state.city'].sudo().search([]).mapped("name")
        vehicles_types_data = self.env['vehicle.vehicle.type'].sudo().search([]).mapped("name")
        ticket_stage_data = self.env['ticket.stage'].sudo().search([]).mapped("name")
        regions_data = self.env['sales.region'].sudo().search([]).mapped("name")
        bulk_import_model = None
        customer_names = []
        if data.get('context').get('active_id'):
            active_id = int(data.get('context').get('active_id'))
            bulk_import_model = self.env[data.get('context').get('active_model')].browse(active_id)
            customer_names = sorted(bulk_import_model.customer_id.mapped("name"))
        rate_type = ['Lane Wise','Tonnage Wise']

        domain = ['|',('groups_id', 'in', self.env.ref('qwqer_ticket_management.helpdesk_user').id),
                  ('groups_id', 'in', self.env.ref('qwqer_ticket_management.helpdesk_manager').id)]
        users = self.env['res.users'].sudo().search(domain)
        users_list = [user.name or '' for user in users]

        column_settings = string.ascii_uppercase[:18] if not self._context.get('download_template',
                                                                               False) else string.ascii_uppercase[:15]
        master_sheet = workbook.add_worksheet("MasterList")
        master_sheet.hidden = 1
        city_row = 0
        for rec in city_data:
            master_sheet.write(city_row, 0, rec or '', design_formats['normal_format'])
            city_row += 1
        users_row = 0
        for rec in users_list:
            master_sheet.write(users_row, 1, rec or '', design_formats['normal_format'])
            users_row += 1
        row = 0
        for customer in customer_names:
            master_sheet.write(row, 2, customer or '', design_formats['normal_format'])
            row += 1
        stage_row = 0
        for stage in ticket_stage_data:
            master_sheet.write(stage_row, 3, stage or '', design_formats['normal_format'])
            stage_row += 1
        regions_row = 0
        for region in regions_data:
            master_sheet.write(regions_row, 4, region or '', design_formats['normal_format'])
            regions_row += 1
        for i in column_settings:
            worksheet.set_column(f'{i}:{i}', 17)
        headers = [
            'Opportunity Name', 'Customer Name', 'Enquiry Generated By', 'Type of Vehicle',
            'Source', 'Destination', 'Tonnage', 'No. Of Vehicles','Target Rate',
            'Vendor Rate', 'Rate Type', 'Vendor Rate Given By', 'Assigned User', 'Region',
            'Vehicle Type Comments', 'Traffic Team Comment'
        ]
        row_range = False
        # Header titles based on the context
        if self._context.get('download_template', False):
            worksheet.set_row(0, 50)
            self.write_headers(worksheet, design_formats, headers)
            row_range = self.get_row_range(headers)
        elif self._context.get('download_import_failed_tickets', False):
            active_id = int(data.get('context').get('active_id'))
            active_model = self.env[data.get('context').get('active_model')].browse(active_id)
            for rec in active_model:
                original_file_data = base64.b64decode(rec.upload_file)
                # Open the original Excel file using xlrd
                workbook = xlrd.open_workbook(file_contents=original_file_data)
                sheet = workbook.sheet_by_index(0)
                self.write_headers(worksheet, design_formats, sheet.row_values(0))
                row_range = self.get_row_range(sheet.row_values(0))
                failed_rows = [line.row_no for line in rec.bulk_import_line_ids if line.state == 'fail']
                for idx, row_num in enumerate(failed_rows):
                    for col_index in range(sheet.ncols):
                        worksheet.write(idx + 1, col_index, sheet.cell_value(row_num - 1, col_index))
        else:
            headers = [
                'Enquiry Number', 'Opportunity Name', 'Customer Name', 'Enquiry Generated By',
                'Type of Vehicle', 'Source', 'Destination', 'Tonnage', 'No. Of Vehicles',
                'Target Rate', 'Vendor Rate', 'Rate Type', 'Vendor Rate Given By',
                'Assigned User',  'Region', 'Vehicle Type Comments', 'Traffic Team Comment', 'Stage'
            ]
            worksheet.set_row(0, 50)
            self.write_headers(worksheet, design_formats, headers)
            row_range = self.get_row_range(headers)
            row = 1
            for rec in active_model:
                worksheet.write(row, 0, rec.name or '', design_formats['normal_format'])
                worksheet.write(row, 1, rec.opportunity_name or '', design_formats['normal_format'])
                worksheet.write(row, 2, rec.customer_id.name if rec.is_existing_customer else
                                        rec.customer_name, design_formats['normal_format'])
                worksheet.write(row, 3, rec.enquiry_generated_by_id.name or '', design_formats['normal_format'])
                worksheet.write(row, 4, rec.vehicle_type_id.name or '', design_formats['normal_format'])
                worksheet.write(row, 5, rec.source_id.name or '', design_formats['normal_format'])
                worksheet.write(row, 6, rec.destination_id.name or '', design_formats['normal_format'])
                worksheet.write(row, 7, rec.tonnage or 0.00, design_formats['float_rate_format'])
                worksheet.write(row, 8, rec.no_of_vehicles or 0, design_formats['int_rate_format'])
                worksheet.write(row, 9, rec.target_rate or 0.00, design_formats['float_rate_format'])
                worksheet.write(row, 10, rec.vendor_rate or 0.00, design_formats['float_rate_format'])
                worksheet.write(row, 11, 'Lane Wise' if rec.rate_type == 'lane_wise' else 'Tonnage Wise'
                                        if rec.rate_type == 'tonnage_wise' else '', design_formats['normal_format'])
                worksheet.write(row, 12, rec.vendor_rate_by_id.name or '', design_formats['normal_format'])
                worksheet.write(row, 13, rec.assigned_user.name or '', design_formats['normal_format'])
                worksheet.write(row, 14, rec.region_id.name or '', design_formats['normal_format'])
                worksheet.write(row, 15, rec.vehicle_type_comment or '', design_formats['normal_format'])
                worksheet.write(row, 16, rec.traffic_team_comment or '', design_formats['normal_format'])
                worksheet.write(row, 17, rec.stage_id.name or '', design_formats['normal_format'])
                row += 1

        if row_range:
            validation_data = {'enquiry_generated_row': {'row_range': row_range['enquiry_generated_row_range'],
                                                      'source': f"=MasterList!$B$1:$B${len(users_list)}",
                                                      'error_message': 'Please select a user from the list.'},
                               'vehicles_types_row': {'row_range': row_range['vehicles_types_row_range'],
                                                      'source': vehicles_types_data,
                                                      'error_message': 'Please select a vehicle type from the list.'},
                               'source_row': {'row_range': row_range['source_row_range'],
                                              'source': f"=MasterList!$A$1:$A${len(city_data)}",
                                              'error_message': 'Please select a source from the list.'},
                               'destination_row': {'row_range': row_range['destination_row_range'],
                                                   'source': f"=MasterList!$A$1:$A${len(city_data)}",
                                                   'error_message': 'Please select a destination from the list.'},
                               'rate_type_row': {'row_range': row_range['rate_type_row_range'],
                                                   'source': rate_type,
                                                   'error_message': 'Please select a Rate Type from the list.'},
                               'rate_given_by_row': {'row_range': row_range['rate_given_by_row_range'],
                                                         'source': f"=MasterList!$B$1:$B${len(users_list)}",
                                                         'error_message': 'Please select a user from the list.'},
                               'assigned_user_row': {'row_range': row_range['assigned_user_row_range'],
                                                     'source': f"=MasterList!$B$1:$B${len(users_list)}",
                                                     'error_message': 'Please select a user from the list.'},
                               'region_row': {'row_range': row_range['region_row_range'],
                                                     'source': f"=MasterList!$E$1:$E${len(regions_data)}",
                                                     'error_message': 'Please select a region from the list.'},
                               }
            if bulk_import_model and bulk_import_model.upload_type == 'existing':
                validation_data.update({
                    'customer_name_row': {
                        'row_range': row_range['customer_name_row_range'],
                        'source': f"=MasterList!$C$1:$C${len(customer_names)}",
                        'error_message': 'Please select the customer from the list.'
                    }
                })
            if not self._context.get('download_template') and not self._context.get('download_import_failed_tickets'):
                validation_data.update({
                    'ticket_stage_row': {
                        'row_range': row_range['stage_row_range'],
                        'source': f"=MasterList!$D$1:$D${len(ticket_stage_data)}",
                        'error_message': 'Please select a stage from the list.'}
                })

            for key, val in validation_data.items():
                worksheet.data_validation(val['row_range'], {'validate': 'list',
                                                             'source': val['source'],
                                                             'error_title': 'Invalid input',
                                                             'error_message': val['error_message']})
