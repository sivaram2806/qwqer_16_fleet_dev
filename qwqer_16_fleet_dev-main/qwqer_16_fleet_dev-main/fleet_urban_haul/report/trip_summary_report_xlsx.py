# -*- coding: utf-8 -*-
from odoo import models


class TripSummaryXlsx(models.AbstractModel):
    _name = 'report.fleet_urban_haul.trip_summary_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Customer and Vendor trip summary xlsx report '

    def generate_xlsx_report(self, workbook, data, active_model):
        """xlsx report generator"""
        # FORMATS STARTS
        design_formats = {
            'heading_format': workbook.add_format({'align': 'center',
                                                   'valign': 'vcenter',
                                                   'bold': True, 'size': 20,
                                                   'font_name': 'Times New Roman',
                                                   # 'bg_color': 'blue', 'color' : 'white',
                                                   'text_wrap': True, 'shrink': True}),
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
                                                     'bg_color': 'FFFFCC',
                                                     'color': 'black',
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
                                                  'size': 11, 'text_wrap': True, 'italic': True, 'bold': True, }),
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
        }

        if active_model.action_type == 'vendor':
            worksheet = workbook.add_worksheet("vendor_trip_summary")
            worksheet.merge_range(1, 2, 2, 4, 'Vendor Trip Summary', design_formats['heading_format'])
        else:
            worksheet = workbook.add_worksheet("customer_trip_summary")
            worksheet.merge_range(1, 2, 2, 4, 'Customer Trip Summary', design_formats['heading_format'])

        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 35)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 20)
        worksheet.set_column('J:J', 20)
        worksheet.set_column('K:K', 20)
        worksheet.set_column('L:L', 20)
        worksheet.set_column('M:M', 20)
        worksheet.set_column('N:N', 20)
        worksheet.set_column('O:O', 20)

        worksheet.write(4, 1, 'From Date', design_formats['bold'])
        worksheet.write(4, 2, active_model.from_date or '', design_formats['date_format'])
        worksheet.write(5, 1, 'Region', design_formats['bold'])
        worksheet.write(5, 2, active_model.region_id.name or '', design_formats['normal_format_central'])
        worksheet.write(4, 4, 'To Date', design_formats['bold'])
        worksheet.write(4, 5, active_model.to_date or '', design_formats['date_format'])

        worksheet.write(8, 0, 'Vehicle Req No', design_formats['heading_format_2'])
        if active_model.action_type == 'customer':
            worksheet.write(8, 1, 'Customer', design_formats['heading_format_2'])
        elif active_model.action_type == 'vendor':
            worksheet.write(8, 1, 'Vendor', design_formats['heading_format_2'])
        worksheet.write(8, 2, 'Sales Person', design_formats['heading_format_2'])
        worksheet.write(8, 3, 'Vehicle No', design_formats['heading_format_2'])
        worksheet.write(8, 4, 'Vehicle Model', design_formats['heading_format_2'])
        worksheet.write(8, 5, 'Vehicle Pricing', design_formats['heading_format_2'])
        worksheet.write(8, 6, 'Driver', design_formats['heading_format_2'])
        worksheet.write(8, 7, 'Status', design_formats['heading_format_2'])
        worksheet.write(8, 8, 'Trip Date', design_formats['heading_format_2'])
        worksheet.write(8, 9, 'Start Time', design_formats['heading_format_2'])
        worksheet.write(8, 10, 'End Time', design_formats['heading_format_2'])
        worksheet.write(8, 11, 'Start Odo', design_formats['heading_format_2'])
        worksheet.write(8, 12, 'End Odo', design_formats['heading_format_2'])
        worksheet.write(8, 13, 'Total Odo', design_formats['heading_format_2'])
        if active_model.action_type == 'vendor':
            worksheet.write(8, 14, 'Vendor Amount', design_formats['heading_format_2'])
        elif active_model.action_type == 'customer':
            worksheet.write(8, 14, 'Customer Amount', design_formats['heading_format_2'])

        total = 0
        row = 8
        col = 0
        domain = [('region_id', '=', active_model.region_id.id), ('trip_date', '>=', active_model.from_date),
                  ('trip_date', '<=', active_model.to_date)]

        if active_model.action_type == 'vendor':
            if active_model.vendor_id:
                domain.append(('vendor_id', '=', active_model.vendor_id.id))
                if active_model.sales_person_id:
                    domain.append(('batch_trip_uh_id.sales_person_id', '=', active_model.sales_person_id.id))
            else:
                if active_model.sales_person_id:
                    domain.append(('batch_trip_uh_id.sales_person_id', '=', active_model.sales_person_id.id))

        elif active_model.action_type == 'customer':
            if active_model.customer_id:
                domain.append(('customer_id', '=', active_model.customer_id.id))
                if active_model.sales_person_id:
                    domain.append(('batch_trip_uh_id.sales_person_id', '=', active_model.sales_person_id.id))
            else:
                if active_model.sales_person_id:
                    domain.append(('batch_trip_uh_id.sales_person_id', '=', active_model.sales_person_id.id))

        batch_trip_line_ids = self.env['batch.trip.uh.line'].search(domain, order='trip_date asc')

        if batch_trip_line_ids:
            for line in batch_trip_line_ids:
                if active_model.from_date <= line.trip_date <= active_model.to_date:
                    row += 1
                    end_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line.end_time) * 60, 60))
                    start_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line.start_time) * 60, 60))

                    worksheet.write(row, col, line.batch_trip_uh_id.name or '',
                                    design_formats['normal_format_central_border'])
                    if active_model.action_type == 'customer':
                        worksheet.write(row, col + 1, line.customer_id.name or '',
                                        design_formats['normal_format_central_border'])
                    elif active_model.action_type == 'vendor':
                        worksheet.write(row, col + 1, line.vendor_id.name or '',
                                        design_formats['normal_format_central_border'])
                    if active_model.action_type == 'customer':
                        worksheet.write(row, col + 2, line.batch_trip_uh_id.sales_person_id.name or '',
                                        design_formats['normal_format_central_border'])
                    elif active_model.action_type == 'vendor':
                        worksheet.write(row, col + 2, line.batch_trip_uh_id.sales_person_id.name or '',
                                        design_formats['normal_format_central_border'])
                    worksheet.write(row, col + 3, line.vehicle_pricing_line_id.vehicle_no.vehicle_no or '',
                                    design_formats['normal_format_central_border'])
                    worksheet.write(row, col + 4, line.vehicle_model_id.name or '',
                                    design_formats['normal_format_central_border'])
                    worksheet.write(row, col + 5, line.vehicle_pricing_id.name or '',
                                    design_formats['normal_format_central_border'])
                    worksheet.write(row, col + 6, line.driver_name or '',
                                    design_formats['normal_format_central_border'])
                    worksheet.write(row, col + 7, dict(line.batch_trip_uh_id._fields['state'].selection).get(
                        line.batch_trip_uh_id.state) or '', design_formats['normal_format_central_border'])
                    worksheet.write(row, col + 8, line.trip_date or '', design_formats['date_format_border'])
                    worksheet.write(row, col + 9, start_time or '', design_formats['normal_format_central_border'])
                    worksheet.write(row, col + 10, end_time or '', design_formats['normal_format_central_border'])
                    worksheet.write(row, col + 11, line.start_km or 0.0, design_formats['float_format'])
                    worksheet.write(row, col + 12, line.end_km or 0.0, design_formats['float_format'])
                    worksheet.write(row, col + 13, line.total_km or 0.0, design_formats['float_format'])
                    if active_model.action_type == 'vendor':
                        worksheet.write(row, col + 14, line.vendor_amount or 0.0, design_formats['amount_format'])
                        total += line.vendor_amount
                    elif active_model.action_type == 'customer':
                        worksheet.write(row, col + 14, line.customer_amount or 0.0, design_formats['amount_format'])
                        total += line.customer_amount

        row += 1
        worksheet.write(row, 0, 'Total', design_formats['bold_border'])
        worksheet.write(row, 1, '', design_formats['bold_border'])
        worksheet.write(row, 2, '', design_formats['bold_border'])
        worksheet.write(row, 3, '', design_formats['bold_border'])
        worksheet.write(row, 4, '', design_formats['bold_border'])
        worksheet.write(row, 5, '', design_formats['bold_border'])
        worksheet.write(row, 6, '', design_formats['bold_border'])
        worksheet.write(row, 7, '', design_formats['bold_border'])
        worksheet.write(row, 8, '', design_formats['bold_border'])
        worksheet.write(row, 9, '', design_formats['bold_border'])
        worksheet.write(row, 10, '', design_formats['bold_border'])
        worksheet.write(row, 11, '', design_formats['bold_border'])
        worksheet.write(row, 12, '', design_formats['bold_border'])
        worksheet.write(row, 13, '', design_formats['bold_border'])
        worksheet.write(row, 14, total or 0.0, design_formats['amount_format_2'])

        row += 2
        worksheet.write(row + 1, 0, 'QWQER', design_formats['bold'])
        worksheet.merge_range(row + 2, 0, row + 2, 1, 'Delivering to the Point', design_formats['bold'])
