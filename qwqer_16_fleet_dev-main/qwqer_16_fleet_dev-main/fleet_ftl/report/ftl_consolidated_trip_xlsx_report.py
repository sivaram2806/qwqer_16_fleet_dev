from odoo import models


class ConsoldatedFTLTripXlsx(models.AbstractModel):
    _name = 'report.fleet_ftl.report_ftl_consolidated_trip_xlsx'
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
                                                              'align': 'center', }),
                          'bold_border': workbook.add_format({'bold': True, 'font_name': 'Times New Roman',
                                                              'size': 11, 'text_wrap': True,
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
                                                                        'border': True, }),
                          'amount_format': workbook.add_format({'num_format': '#,##0.00',
                                                                'font_name': 'Times New Roman',
                                                                'align': 'right', 'size': 11,
                                                                'text_wrap': True}),
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

        worksheet = workbook.add_worksheet("FTL Consolidated Trip")

        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 33)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 25)
        worksheet.set_column('F:F', 25)
        worksheet.set_column('G:G', 25)
        worksheet.set_column('H:H', 25)
        worksheet.set_column('I:I', 25)

        worksheet.write(3, 1, 'Customer', design_formats['bold'])
        worksheet.write(3, 2, active_model.customer_id.name or '', design_formats['normal_format_central'])
        worksheet.write(3, 4, 'Region', design_formats['bold'])
        worksheet.write(3, 5, active_model.region_id.name or '', design_formats['normal_format_central'])
        worksheet.write(4, 1, 'From Date', design_formats['bold'])
        worksheet.write(4, 2, active_model.from_date or '', design_formats['date_format'])
        worksheet.write(4, 4, 'To Date', design_formats['bold'])
        worksheet.write(4, 5, active_model.to_date or '', design_formats['date_format'])

        worksheet.write(7, 0, 'Trip No', design_formats['heading_format_2'])
        worksheet.write(7, 1, 'Trip Date', design_formats['heading_format_2'])
        worksheet.write(7, 2, 'Total Km', design_formats['heading_format_2'])
        worksheet.write(7, 3, 'Amount', design_formats['heading_format_2'])

        total_km = 0
        total_amount = 0
        row = 7
        col = 0

        for line in active_model.trip_summary_ftl_line_ids:
            row += 1

            worksheet.write(row, col, line.name or '', design_formats['normal_format_central'])
            worksheet.write(row, col + 1, line.trip_date or '', design_formats['date_format'])
            worksheet.write(row, col + 2, line.total_lines_km or 0.0, design_formats['float_format'])
            worksheet.write(row, col + 3, line.total_lines_amount or 0.0, design_formats['float_format'])
            total_km += line.total_lines_km
            total_amount += line.total_lines_amount

        row += 1
        worksheet.write(row, 0, 'Total', design_formats['bold_border'])
        worksheet.write(row, 1, '', design_formats['bold_border'])
        worksheet.write(row, 2, total_km or 0.0, design_formats['amount_format_2'])
        worksheet.write(row, 3, total_amount or 0.0, design_formats['amount_format_2'])

        row += 2
        worksheet.write(row + 1, 0, 'QWQER', design_formats['bold'])
        worksheet.merge_range(row + 2, 0, row + 2, 1, 'Delivering to the Point', design_formats['bold'])

        worksheet = workbook.add_worksheet("FTL Consolidated Trip Line")

        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 25)
        worksheet.set_column('F:F', 25)
        worksheet.set_column('G:G', 25)
        worksheet.set_column('H:H', 25)
        worksheet.set_column('I:I', 25)

        row = 0

        for trip in active_model.trip_summary_ftl_line_ids:
            row += 3
            worksheet.write(row, 1, 'Trip Number', design_formats['bold'])
            worksheet.write(row, 2, trip.name or '', design_formats['normal_format_central'])

            worksheet.write(row + 2, 0, 'Trip No', design_formats['heading_format_2'])
            worksheet.write(row + 2, 1, 'Vehicle Number', design_formats['heading_format_2'])
            worksheet.write(row + 2, 2, 'Vehicle Model', design_formats['heading_format_2'])
            worksheet.write(row + 2, 3, 'Start Date', design_formats['heading_format_2'])
            worksheet.write(row + 2, 4, 'End Date', design_formats['heading_format_2'])
            worksheet.write(row + 2, 5, 'Total Km', design_formats['heading_format_2'])
            worksheet.write(row + 2, 6, 'Amount', design_formats['heading_format_2'])

            row = row + 2
            col = 0


            row += 1
            worksheet.write(row, col, trip.ftl_batch_trip_id.name or '', design_formats['normal_format_central'])
            worksheet.write(row, col + 1, trip.ftl_batch_trip_id.vehicle_id.vehicle_no or '', design_formats['normal_format_central'])
            worksheet.write(row, col + 2, trip.ftl_batch_trip_id.vehicle_model_id.display_name or '', design_formats['normal_format_central'])
            worksheet.write(row, col + 3, trip.ftl_batch_trip_id.start_date or 0.0, design_formats['date_format'])
            worksheet.write(row, col + 4, trip.ftl_batch_trip_id.end_date or 0.0, design_formats['date_format'])
            worksheet.write(row, col + 5, trip.ftl_batch_trip_id.total_km or 0.0, design_formats['float_format'])
            worksheet.write(row, col + 6, trip.ftl_batch_trip_id.total_amount or 0.0, design_formats['float_format'])
            total_km += trip.ftl_batch_trip_id.total_km
            total_amount += trip.ftl_batch_trip_id.total_km
        row += 1
        worksheet.write(row, 0, 'Total', design_formats['bold_border'])
        worksheet.write(row, 1, '', design_formats['bold_border'])
        worksheet.write(row, 2, '', design_formats['bold_border'])
        worksheet.write(row, 3, '', design_formats['bold_border'])
        worksheet.write(row, 4, '', design_formats['bold_border'])
        worksheet.write(row, 5, total_km or 0.0, design_formats['amount_format_2'])
        worksheet.write(row, 6, total_amount or 0.0, design_formats['amount_format_2'])
