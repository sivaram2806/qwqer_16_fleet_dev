from odoo import fields, models, api, _


class BatchTripXlsx(models.AbstractModel):
    _name = 'report.fleet_urban_haul.report_batch_trip_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    def generate_xlsx_report(self, workbook, data, active_model):
        # FORMATS STARTS
        design_formats = {'heading_format': workbook.add_format({'align': 'center',
                                                                 'valign': 'vcenter',
                                                                 'bold': True, 'size': 11,
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
                                                              'align': 'center',}),
                          'bold_border': workbook.add_format({'bold': True, 'font_name': 'Times New Roman',
                                                              'size': 11,'text_wrap': True,
                                                              'border': True,}),
                          'date_format': workbook.add_format({'num_format': 'dd/mm/yyyy',
                                                              'font_name': 'Times New Roman', 'size': 11,
                                                              'align': 'center', 'text_wrap': True,
                                                              'border': True,}),
                          'datetime_format': workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm:ss',
                                                                  'font_name': 'Times New Roman', 'size': 11,
                                                                  'align': 'center', 'text_wrap': True}),
                          'normal_format': workbook.add_format({'font_name': 'Times New Roman',
                                                                'size': 11, 'text_wrap': True,'italic': True,'bold': True,}),
                          'normal_format_right': workbook.add_format({'font_name': 'Times New Roman',
                                                                      'align': 'right', 'size': 11,
                                                                      'text_wrap': True}),
                          'normal_format_central': workbook.add_format({'font_name': 'Times New Roman',
                                                                        'size': 11, 'align': 'center',
                                                                        'text_wrap': True,
                                                                        'border': True,}),
                          'amount_format': workbook.add_format({'num_format': '#,##0.00',
                                                                'font_name': 'Times New Roman',
                                                                'align': 'right', 'size': 11,
                                                                'text_wrap': True}),
                          'amount_format_2': workbook.add_format({'num_format': '#,##0.00',
                                                                  'font_name': 'Times New Roman',
                                                                  'bold': True,
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True,
                                                                  'border': True,}),
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
                                                                    'border': True,}),
                          'int_rate_format': workbook.add_format({'num_format': '###0',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True}),
                                                                  }
        
        worksheet = workbook.add_worksheet("batch_trip")
        
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 30)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 25)
        worksheet.set_column('F:F', 25)
        worksheet.set_column('G:G', 25)
        worksheet.set_column('H:H', 25)
        worksheet.set_column('I:I', 25)
        
        worksheet.write(3, 1, 'Customer Name', design_formats['heading_format_1'])
        worksheet.write(3, 2, active_model.customer_id.name or '', design_formats['normal_format_central'])
        worksheet.write(4, 1, 'Region', design_formats['heading_format_1'])
        worksheet.write(4, 2, active_model.region_id.name or '', design_formats['normal_format_central'])
        worksheet.write(3, 4, 'Phone', design_formats['heading_format_1'])
        worksheet.write(3, 5, active_model.customer_id.phone or '', design_formats['normal_format_central'])
        worksheet.write(4, 4, 'Address', design_formats['heading_format_1'])
        worksheet.write(4, 5, active_model.customer_id.state_id.name or '', design_formats['normal_format_central'])
        
        worksheet.write(7, 0, 'Vehicle No', design_formats['heading_format_2'])
        worksheet.write(7, 1, 'Trip Date', design_formats['heading_format_2'])
        worksheet.write(7, 2, 'Start Time', design_formats['heading_format_2'])
        worksheet.write(7, 3, 'End Time', design_formats['heading_format_2'])
        worksheet.write(7, 4, 'Start Odo', design_formats['heading_format_2'])
        worksheet.write(7, 5, 'End Odo', design_formats['heading_format_2'])
        worksheet.write(7, 6, 'Total Odo', design_formats['heading_format_2'])
        
        total=0 
        row=7
        col=0   

        for line in active_model.batch_trip_uh_line_ids:
            row += 1
            end_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line.end_time)* 60, 60))
            start_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line.start_time)* 60, 60))
            
            worksheet.write(row, col, line.vehicle_pricing_line_id.vehicle_no.vehicle_no or '', design_formats['normal_format_central'])
            worksheet.write(row, col+1, line.trip_date or '', design_formats['date_format'])
            worksheet.write(row, col+2, start_time or '', design_formats['normal_format_central'])
            worksheet.write(row, col+3, end_time or '', design_formats['normal_format_central'])
            worksheet.write(row, col+4, line.start_km or 0.0, design_formats['float_format'])
            worksheet.write(row, col+5, line.end_km or 0.0, design_formats['float_format'])
            worksheet.write(row, col+6, line.total_km or 0.0, design_formats['float_format'])
            total += line.total_km
        
        row +=1
        worksheet.write(row, 0, 'Total', design_formats['bold_border'])
        worksheet.write(row, 1, '', design_formats['bold_border'])
        worksheet.write(row, 2, '', design_formats['bold_border'])
        worksheet.write(row, 3, '', design_formats['bold_border'])
        worksheet.write(row, 4, '', design_formats['bold_border'])
        worksheet.write(row, 5, '', design_formats['bold_border'])
        worksheet.write(row, 6, total or 0.0, design_formats['amount_format_2'])
        
        row += 2
        worksheet.merge_range(row,0,row,2, 'For any clarification please reach out mail  support@qwqer.in', design_formats['normal_format'])
        worksheet.write(row+2,0,'QWQER', design_formats['bold'])
        worksheet.merge_range(row+3,0,row+3,1, 'Delivering to the Point', design_formats['bold'])
        
           
            
            


        
        
        
        