from odoo import models, api, _


class CostAnalysisReportXlsx(models.AbstractModel):
    _name = 'report.fleet_urban_haul.cost_analysis_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Const Analysis xlsx report for Non FTL services'

    def generate_xlsx_report(self, workbook, data, active_model):
        """
        method to generate xlsx report
        @param workbook:
        @param data:
        @param active_model:
        """
        # FORMATS STARTS
        design_formats = {
            'heading_format': workbook.add_format({'align': 'center',
                                                   'valign': 'vcenter',
                                                   'bold': True, 'size': 25,
                                                   'font_name': 'Times New Roman',
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

        worksheet = workbook.add_worksheet("Cost Analysis Report")

        worksheet.merge_range(1, 5, 2, 6, 'Cost Analysis Report', design_formats['heading_format'])

        worksheet.set_column('A:A', 13)
        worksheet.set_column('B:B', 13)

        worksheet.set_column('C:C', 17)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 36)
        worksheet.set_column('G:G', 36)
        worksheet.set_column('H:H', 18)
        worksheet.set_column('I:I', 28)

        worksheet.set_column('J:J', 20)
        worksheet.set_column('K:K', 20)
        worksheet.set_column('L:L', 25)

        worksheet.set_column('M:M', 20)
        worksheet.set_column('N:N', 13)
        worksheet.set_column('O:O', 13)
        worksheet.set_column('P:P', 13)
        worksheet.set_column('Q:Q', 13)
        worksheet.set_column('R:R', 13)
        worksheet.set_column('S:S', 17)
        worksheet.set_column('T:T', 15)
        worksheet.set_column('U:U', 13)
        worksheet.set_column('V:V', 20)

        worksheet.write(4, 4, 'From Date', design_formats['bold'])
        worksheet.write(4, 5, active_model.from_date or '', design_formats['date_format'])
        worksheet.write(4, 6, 'To Date', design_formats['bold'])
        worksheet.write(4, 7, active_model.to_date or '', design_formats['date_format'])

        worksheet.write(7, 0, 'Trip Date', design_formats['heading_format_2'])
        worksheet.write(7, 1, 'Trip No', design_formats['heading_format_2'])
        worksheet.write(7, 2, 'Vehicle Req No', design_formats['heading_format_2'])
        worksheet.write(7, 3, 'Status', design_formats['heading_format_2'])
        worksheet.write(7, 4, 'Sales Person', design_formats['heading_format_2'])
        worksheet.write(7, 5, 'Vendor', design_formats['heading_format_2'])
        worksheet.write(7, 6, 'Customer', design_formats['heading_format_2'])
        worksheet.write(7, 7, 'Region', design_formats['heading_format_2'])
        worksheet.write(7, 8, 'Vehicle No', design_formats['heading_format_2'])
        worksheet.write(7, 9, 'Vehicle Model', design_formats['heading_format_2'])
        worksheet.write(7, 10, 'Vehicle Pricing', design_formats['heading_format_2'])
        worksheet.write(7, 11, 'Vehicle Description', design_formats['heading_format_2'])
        worksheet.write(7, 12, 'Driver', design_formats['heading_format_2'])
        worksheet.write(7, 13, 'Start Time', design_formats['heading_format_2'])
        worksheet.write(7, 14, 'End Time', design_formats['heading_format_2'])
        worksheet.write(7, 15, 'Start Odo', design_formats['heading_format_2'])
        worksheet.write(7, 16, 'End Odo', design_formats['heading_format_2'])
        worksheet.write(7, 17, 'Total Odo', design_formats['heading_format_2'])
        worksheet.write(7, 18, 'Customer Amount', design_formats['heading_format_2'])
        worksheet.write(7, 19, 'Vendor Amount', design_formats['heading_format_2'])
        worksheet.write(7, 20, 'Margin', design_formats['heading_format_2'])
        worksheet.write(7, 21, 'Percentage Difference', design_formats['heading_format_2'])

        row = 7
        col = 0
        domain = [('trip_date', '>=', active_model.from_date), ('trip_date', '<=', active_model.to_date),
                  ('batch_trip_uh_id.state', 'in', ('completed', 'approved'))]

        if active_model.vendor_id:
            domain.append(('vendor_id', '=', active_model.vendor_id.id))

        if active_model.customer_id:
            domain.append(('customer_id', '=', active_model.customer_id.id))

        if active_model.region_id:
            domain.append(('region_id', '=', active_model.region_id.id))

        if active_model.vehicle_pricing_id:
            domain.append(('vehicle_pricing_id', '=', active_model.vehicle_pricing_id.id))

        if active_model.sales_person_id:
            domain.append(('batch_trip_uh_id.sales_person_id', '=', active_model.sales_person_id.id))

        batch_trip_line_ids = self.env['batch.trip.uh.line'].search(domain, order='trip_date asc')
        if batch_trip_line_ids:
            for line in batch_trip_line_ids:
                row += 1
                customer_amount = 0.0
                vendor_amount = 0.0

                if line.calculation_frequency == 'daily':
                    customer_amount = line.customer_amount
                else:
                    batch_trip_line = batch_trip_line_ids.filtered(
                        lambda s: s.trip_date <= line.trip_date and s.customer_id.id == line.customer_id.id and
                        s.region_id.id == line.region_id.id and
                        s.vehicle_pricing_line_id.id == line.vehicle_pricing_line_id.id)

                    start_time = sum(batch_trip_line.mapped('start_time')) or 0.0
                    end_time = sum(batch_trip_line.mapped('end_time')) or 0.0
                    total_time = end_time - start_time
                    start_km = sum(batch_trip_line.mapped('start_km')) or 0.0
                    end_km = sum(batch_trip_line.mapped('end_km')) or 0.0
                    total_km = end_km - start_km
                    if line.customer_id.partner_vehicle_pricing_ids:
                        vehicle_pricing_id = self.env['partner.vehicle.pricing'].search(
                            [('partner_id', '=', line.customer_id.id),
                             ('vehicle_pricing_id', '=', line.vehicle_pricing_id.id)], limit=1)
                        if vehicle_pricing_id:
                            customer_amount = self.calculate_km_hour_cost(vehicle_pricing_id, total_km, total_time)

                if line.vendor_calculation_frequency == 'daily':
                    vendor_amount = line.vendor_amount
                else:
                    batch_trip_line = batch_trip_line_ids.filtered(lambda s: s.trip_date <= line.trip_date and
                                                                             s.vendor_id.id == line.vendor_id.id and
                                                                             s.region_id.id == line.region_id.id and
                                                                             s.vehicle_pricing_line_id.id == line.vehicle_pricing_line_id.id)

                    start_time = sum(batch_trip_line.mapped('start_time')) or 0.0
                    end_time = sum(batch_trip_line.mapped('end_time')) or 0.0
                    total_time = end_time - start_time
                    start_km = sum(batch_trip_line.mapped('start_km')) or 0.0
                    end_km = sum(batch_trip_line.mapped('end_km')) or 0.0
                    total_km = end_km - start_km
                    if line.vendor_id.partner_vehicle_pricing_ids:
                        vehicle_pricing_id = self.env['partner.vehicle.pricing'].search([('partner_id', '=', line.vendor_id.id),
                                                                                 ('vehicle_pricing_id', '=',
                                                                                  line.vehicle_pricing_id.id)], limit=1)
                        if vehicle_pricing_id:
                            vendor_amount = self.calculate_km_hour_cost(vehicle_pricing_id, total_km, total_time)

                margin = customer_amount - vendor_amount
                percentage_difference = 0
                if customer_amount > 0:
                    percentage_difference = (margin / customer_amount) * 100
                end_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line.end_time) * 60, 60))
                start_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line.start_time) * 60, 60))

                worksheet.write(row, col, line.trip_date or '', design_formats['date_format_border'])
                worksheet.write(row, col + 1, line.trip_no or '', design_formats['normal_format_central_border'])
                worksheet.write(row, col + 2, line.batch_trip_uh_id.name or '',
                                design_formats['normal_format_central_border'])
                worksheet.write(row, col + 3, dict(line.batch_trip_uh_id._fields['state'].selection).get(
                    line.batch_trip_uh_id.state) or '', design_formats['normal_format_central_border'])
                worksheet.write(row, col + 4, line.batch_trip_uh_id.sales_person_id.name or '',
                                design_formats['normal_format_central_border'])
                worksheet.write(row, col + 5, line.vendor_id.name or '', design_formats['normal_format_central_border'])
                worksheet.write(row, col + 6, line.customer_id.name or '',
                                design_formats['normal_format_central_border'])
                worksheet.write(row, col + 7, line.region_id.name or '', design_formats['normal_format_central_border'])
                worksheet.write(row, col + 8, line.vehicle_pricing_line_id.vehicle_no.vehicle_no or '',
                                design_formats['normal_format_central_border'])
                worksheet.write(row, col + 9, line.vehicle_model_id.name or '',
                                design_formats['normal_format_central_border'])
                worksheet.write(row, col + 10, line.vehicle_pricing_id.name or '',
                                design_formats['normal_format_central_border'])
                worksheet.write(row, col + 11, line.vehicle_pricing_line_id.vehicle_description or '',
                                design_formats['normal_format_central_border'])
                worksheet.write(row, col + 12, line.driver_name or '', design_formats['normal_format_central_border'])
                worksheet.write(row, col + 13, start_time or '', design_formats['normal_format_central_border'])
                worksheet.write(row, col + 14, end_time or '', design_formats['normal_format_central_border'])
                worksheet.write(row, col + 15, line.start_km or 0.0, design_formats['float_format'])
                worksheet.write(row, col + 16, line.end_km or 0.0, design_formats['float_format'])
                worksheet.write(row, col + 17, line.total_km or 0.0, design_formats['float_format'])
                worksheet.write(row, col + 18, customer_amount or 0.0, design_formats['amount_format'])
                worksheet.write(row, col + 19, vendor_amount or 0.0, design_formats['amount_format'])
                worksheet.write(row, col + 20, margin or 0.0, design_formats['amount_format'])
                worksheet.write(row, col + 21, percentage_difference or 0.0, design_formats['amount_format'])

    @staticmethod
    def calculate_km_hour_cost(vehicle_pricing_id, total_km, total_time):
        """
        To calculate cost by
        @param vehicle_pricing_id:
        @param total_km:
        @param total_time:
        @return: sum(km_cost, hour_cost)
        """
        if total_km <= vehicle_pricing_id.base_dist:
            km_cost = vehicle_pricing_id.base_cost or 0.0
        else:
            km_cost = (((total_km - vehicle_pricing_id.base_dist) * vehicle_pricing_id.charge_per_km)
                       + vehicle_pricing_id.base_cost) or 0.0
        if total_time <= vehicle_pricing_id.base_hrs:
            hour_cost = vehicle_pricing_id.base_cost_hrs or 0.0
        else:
            hour_cost = (((total_time - vehicle_pricing_id.base_hrs) * vehicle_pricing_id.additional_hrs)
                         + vehicle_pricing_id.base_cost_hrs) or 0.0
        return km_cost + hour_cost
