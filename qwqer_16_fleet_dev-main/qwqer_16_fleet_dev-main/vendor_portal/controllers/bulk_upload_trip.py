# -*- coding: utf-8 -*-
from odoo.http import request
from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager
import base64
from odoo.exceptions import ValidationError, UserError
import json
import xlsxwriter
from io import BytesIO
import magic


class PortalBulkTripUpload(CustomerPortal):
    def generate_import_trip_template(self):
        """function to generate vendor bulk upload template"""
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        design_formats = {'heading_format': workbook.add_format({'align': 'center',
                                                                 'valign': 'vcenter',
                                                                 'bold': True, 'size': 25,
                                                                 'font_name': 'Times New Roman',
                                                                 'text_wrap': True,
                                                                 'shrink': True}),
                          'heading_format_1': workbook.add_format({'align': 'left',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   'bg_color': 'FFFFCC',
                                                                   'color': 'black',
                                                                   'border': True,
                                                                   'text_wrap': True, 'shrink': True}),
                          'heading_format_2': workbook.add_format({'align': 'center',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   'color': 'black',
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
                                                              'align': 'center',
                                                              'border': True, }),
                          'bold_border': workbook.add_format({'bold': True, 'font_name': 'Times New Roman',
                                                              'size': 11, 'text_wrap': True,
                                                              'border': True, }),
                          'date_format_border': workbook.add_format({'num_format': 'dd/mm/yyyy',
                                                                     'font_name': 'Times New Roman', 'size': 11,
                                                                     'align': 'center', 'text_wrap': True,
                                                                     'border': True, }),
                          'date_format': workbook.add_format({'num_format': 'dd/mm/yyyy',
                                                              'font_name': 'Times New Roman', 'size': 11,
                                                              'align': 'center', 'text_wrap': True,
                                                              }),
                          'datetime_format': workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm:ss',
                                                                  'font_name': 'Times New Roman', 'size': 11,
                                                                  'align': 'center', 'text_wrap': True}),
                          'normal_format': workbook.add_format({'font_name': 'Times New Roman',
                                                                'size': 11, 'text_wrap': True, 'italic': True,
                                                                'bold': True, }),
                          'normal_format_right': workbook.add_format({'font_name': 'Times New Roman',
                                                                      'align': 'right', 'size': 11,
                                                                      'text_wrap': True}),
                          'normal_format_central': workbook.add_format({'font_name': 'Times New Roman',
                                                                        'size': 11, 'align': 'center',
                                                                        'text_wrap': True,
                                                                        }),
                          'normal_format_central_border': workbook.add_format({'font_name': 'Times New Roman',
                                                                               'size': 11, 'align': 'center',
                                                                               'text_wrap': True,
                                                                               'border': True, }),
                          'amount_format': workbook.add_format({'num_format': '#,##0.00',
                                                                'font_name': 'Times New Roman',
                                                                'align': 'right', 'size': 11,
                                                                'text_wrap': True,
                                                                'border': True, }),
                          'amount_format_2': workbook.add_format({'num_format': '#,##0.00',
                                                                  'font_name': 'Times New Roman',
                                                                  'bold': True,
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True,
                                                                  'border': True, }),
                          'amount_format_1': workbook.add_format({'num_format': '#,##0',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True}),
                          'normal_num_bold': workbook.add_format({'bold': True, 'num_format': '#,##0.00',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True}),
                          'float_format': workbook.add_format({'num_format': '###0.00',
                                                               'font_name': 'Times New Roman',
                                                               'align': 'center', 'size': 11,
                                                               'text_wrap': True,
                                                               'border': True, }),
                          'int_rate_format': workbook.add_format({'num_format': '###0',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True}),
                          'time_format': workbook.add_format({
                                        'num_format': 'hh:mm',
                                        'font_name': 'Times New Roman',
                                        'align': 'center',
                                        'text_wrap': True,
                                        'border': False
                                    })
                          }

        worksheet = workbook.add_worksheet("Bulk Upload Report Template")

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 35)
        worksheet.set_column('C:C', 23)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 30, design_formats['time_format'])  # Start Time column
        worksheet.set_column('F:F', 30, design_formats['time_format'])  # End Time column
        worksheet.set_column('G:G', 25)
        worksheet.set_column('H:H', 25)

        worksheet.write(0, 0, 'SL No. (Mandatory)', design_formats['heading_format_2'])
        worksheet.write(0, 1, 'Trip Date(2023-04-30) (Mandatory)', design_formats['heading_format_2'])
        worksheet.write(0, 2, 'Vehicle No (Mandatory)', design_formats['heading_format_2'])
        worksheet.write(0, 3, 'Comments', design_formats['heading_format_2'])
        worksheet.write(0, 4, 'Start Time(09:00) (Mandatory)', design_formats['heading_format_2'])
        worksheet.write(0, 5, 'End Time(18:30) (Mandatory)', design_formats['heading_format_2'])
        worksheet.write(0, 6, 'Start Odo (Mandatory)', design_formats['heading_format_2'])
        worksheet.write(0, 7, 'End Odo (Mandatory)', design_formats['heading_format_2'])
        worksheet.data_validation('E2:E1048576', {
            'validate': 'custom',
            'value': '=AND(E2>=0,E2<1)',
            'error_title': 'Invalid Time',
            'error_message': 'Please enter a valid time in hh:mm format (between 00:00 and 23:59).'
        })

        worksheet.data_validation('F2:F1048576', {
            'validate': 'custom',
            'value': '=AND(F2>=0,F2<1,F2>E2)',  # Ensure End Time is greater than Start Time
            'error_title': 'Invalid Time',
            'error_message': 'End Time must be greater than Start Time and in hh:mm format (between 00:00 and 23:59).'
        })
        worksheet.data_validation('G2:G1048576', {
            'validate': 'integer',
            'criteria': '>=',
            'value': 0,
            'error_title': 'Invalid Odometer Reading',
            'error_message': 'Start Odo must be a positive integer.'
        })

        worksheet.data_validation('H2:H1048576', {
            'validate': 'custom',
            'value': '=AND(H2>=0,H2>G2)',  # Ensure End Odo is greater than Start Odo
            'error_title': 'Invalid Odometer Reading',
            'error_message': 'End Odo must be greater than Start Odo and a positive integer.'
        })
        partner = request.env.user.partner_id
        company_id = partner.company_id.id
        vehicles = request.env['vehicle.pricing.line'].sudo().search(
            [('vendor_id', '=', partner.id), ('company_id', '=', company_id),
             ('vehicle_pricing_id.company_id', '=', company_id)])

        vehicle_data = [(vehicle.id, vehicle.display_name or '') for vehicle in vehicles]

        # Create a hidden worksheet to store vehicle no
        hidden_sheet = workbook.add_worksheet("Hidden")
        hidden_sheet.hide()

        # Write vehicle names to the hidden sheet
        for i, (vehicle_id, vehicle_name) in enumerate(vehicle_data):
            hidden_sheet.write(i, 0, vehicle_id)
            hidden_sheet.write(i, 1, vehicle_name)

            # Define the range for the vehicle names
        data_range = 'Hidden!$B$1:$B${}'.format(len(vehicle_data))

        # Up to the maximum number of rows in Excel
        worksheet.data_validation('C2:C1048576', {'validate': 'list',
                                                  'source': data_range,
                                                  'error_title': 'Invalid input',
                                                  'error_message': 'Please select a vehicle from the list.'})
        workbook.close()

        # Get the XLSX file data
        output.seek(0)
        xlsx_data = output.read()
        return xlsx_data

    def validate_mime_type(self, file):
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file.read())
        file.seek(0)  # Reset file pointer to the beginning
        valid_mime_types = ['application/vnd.ms-excel',
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
        if mime_type not in valid_mime_types:
            raise ValidationError('Invalid file type. Only XLS and XLSX files are allowed.')

    @http.route(['/trip_Bulk_upload', '/trip_Bulk_upload/page/<int:page>'], type='http', auth="user", website=True,
                sitemap=True)
    def trip_bulk_upload_list_view(self, page=1, search="", search_in=""):
        """function to get bulk upload list and render the list view template"""
        searchbar_inputs = {
            # 'All': {'domain': [("name", "like", search)], 'input': 'All', 'label': _('Search in All')},
            'Name': {'domain': [("name", "ilike", search)], 'input': 'Name', 'label': _('Name')},
            'Status': {'domain': [("state", "ilike", search)], 'input': 'Status', 'label': _('Status')},
            'File Name': {'domain': [("filename", "ilike", search)], 'input': 'File Name', 'label': _('File Name')}
        }
        search_domain = searchbar_inputs[search_in]["domain"]  if search_in else []
        user = request.env.user
        partner = request.env.user.partner_id
        company_id = partner.company_id.id
        domain = [('create_uid', '=', user.id), ('company_id', '=', company_id)]
        domain += search_domain
        upload_count = request.env['bulk.upload.trip'].sudo().search_count(domain)
        page_details = pager(url='/trip_Bulk_upload',
                             total=upload_count,
                             page=page,
                             step=21)
        uploads = request.env['bulk.upload.trip'].sudo().search(domain, limit=21, offset=page_details['offset'])
        vals = {'uploads': uploads, 'page_name': 'trip_Bulk_upload', 'pager': page_details, 'search': search,
                'searchbar_inputs': searchbar_inputs,
                'search_in': search_in}
        return request.render('vendor_portal.portal_trip_Bulk_upload_list', vals)

    @http.route(['/trip_bulk_upload/form'], type='http', methods=['GET', 'POST'], auth="user", website=True,
                sitemap=True)
    def trip_bulk_upload_form(self, **kwargs):
        """function to get bulk upload create form and render the form view template"""
        error = None
        if request.httprequest.method == 'POST':
            try:
                if 'import_file' in request.httprequest.files:
                    import_file = request.httprequest.files['import_file']
                    if not import_file.filename:
                        raise ValidationError('Import File is Required')
                    else:
                        self.validate_mime_type(import_file)
                        file_content = import_file.read()
                        encoded_file = base64.b64encode(file_content)
                        upload_vals = {
                            'upload_file': encoded_file,
                            'filename': import_file.filename,
                        }
                        bulk_import = request.env['bulk.upload.trip'].sudo().create(upload_vals)
                        if not bulk_import:
                            error = "Something Went Wrong"
                        else:
                            return request.redirect(f'/trip_bulk_upload/form/{bulk_import.id}')
            except ValidationError as e:
                error = str(e)
            except UserError as e:
                error = str(e)
            except Exception:
                error = 'somthing went wrong'
        vals = {'page_name': 'trip_Bulk_upload', 'error': error}
        return request.render('vendor_portal.trip_bulk_upload_form', vals)

    @http.route(['/trip_bulk_upload/form/<model("bulk.upload.trip"):bulk_import_id>'], type='http',
                methods=['GET', 'POST'], auth="user", website=True, sitemap=True)
    def trip_bulk_upload(self, bulk_import_id, **kwargs):
        """function to get bulk upload detailed form and render the form view template"""
        error = kwargs.get('error', None)
        if request.httprequest.method == 'POST':
            try:
                if 'import_file' in request.httprequest.files:
                    import_file = request.httprequest.files['import_file']

                    if not import_file.filename:
                        raise ValidationError('Import File is Required')
                    else:
                        self.validate_mime_type(import_file)
                        file_content = import_file.read()
                        encoded_file = base64.b64encode(file_content)
                        upload_vals = {
                            'upload_file': encoded_file,
                            'filename': import_file.filename,
                        }
                        bulk_import_id.sudo().write(upload_vals)
            except ValidationError as e:
                error = str(e)
            except UserError as e:
                error = str(e)
            except Exception:
                error = 'somthing went wrong'
        vals = {'upload': bulk_import_id, 'page_name': 'trip_Bulk_upload',
                'error': error}
        user = request.env.user
        partner = request.env.user.partner_id
        company_id = partner.company_id.id

        import_rec = request.env['bulk.upload.trip'].sudo().search(
            [('create_uid', '=', user.id), ('company_id', '=', company_id)])
        import_ids = import_rec.ids
        current_imp_index = import_ids.index(bulk_import_id.id)

        prev_record = next_record = None
        if current_imp_index != 0:
            prev_record = import_ids[current_imp_index - 1]
        if current_imp_index < len(import_ids) - 1:
            next_record = import_ids[current_imp_index + 1]

        vals['prev_record'] = prev_record and f'/trip_bulk_upload/form/{prev_record}' or None
        vals['next_record'] = next_record and f'/trip_bulk_upload/form/{next_record}' or None

        return request.render('vendor_portal.trip_bulk_upload_form', vals)

    @http.route(['/trip_bulk_upload/import/<model("bulk.upload.trip"):import_id>'],
                type='http', auth='user',
                methods=['POST'], csrf=True)
    def import_trips(self, import_id, **kwargs):
        """function to import bulk upload trips to daily trips create"""
        if request.httprequest.method == 'POST':
            try:
                import_id.import_file()
                response = {'success': True}
            except ValidationError as e:
                response = {'error': str(e)}
            except UserError as e:
                response = {'error': str(e)}
            except Exception:
                response = {'error': "Something went wrong"}

            return request.make_response(json.dumps(response), headers={'Content-Type': 'application/json'})

    @http.route('/bulk_upload/download_template', type='http', auth='user')
    def download_template(self):
        """function to download import bulk upload template xls"""
        import_trip_template = self.generate_import_trip_template()
        return request.make_response(
            import_trip_template,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename=Bulk_Upload_Report_Template.xlsx;')
            ]
        )

    @http.route('/trip_bulk_upload/download/<model("bulk.upload.trip"):record_id>', type='http', auth="user")
    def download_file(self, record_id):
        """function to download uploaded bulk upload xls"""
        record = record_id
        if not record.exists():
            return request.not_found()
        file_content = base64.b64decode(record.upload_file)
        return request.make_response(file_content,
                                     headers=[
                                         ('Content-Type', 'application/octet-stream'),
                                         ('Content-Disposition', f'attachment; filename={record.filename}')
                                     ])

    @http.route('/trip_bulk_upload/cancel/<model("bulk.upload.trip"):record_id>', type='http', auth="user")
    def cancel_import(self, record_id):
        """function to cancel bulk upload record"""
        record = record_id
        if not record.exists():
            return request.not_found()
        record_id.action_cancel()
        return request.redirect(f'/trip_bulk_upload/form/{record_id.id}')
