from odoo import models


class FtlCostAnalysisXlsxReport(models.AbstractModel):
    _name = 'report.fleet_ftl.report_ftl_cost_analysis_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = "FTL Cost analysis report"

    def generate_xlsx_report(self, workbook, data, active_model):
        """method to generate XLSX Cost analysis report"""
        # FORMATS STARTS
        design_formats = {'heading_format': workbook.add_format({'align': 'center',
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
                          }

        work_order_sheet = workbook.add_worksheet("FTL Work Order Cost Analysis")

        work_order_sheet.merge_range(1, 3, 2, 5, 'FTL Work Order Cost Analysis', design_formats['heading_format'])

        work_order_sheet.set_column('A:A', 13)
        work_order_sheet.set_column('B:B', 13)

        work_order_sheet.set_column('C:C', 25)
        work_order_sheet.set_column('D:D', 17)
        work_order_sheet.set_column('E:E', 15)
        work_order_sheet.set_column('F:F', 20)
        work_order_sheet.set_column('G:G', 36)
        work_order_sheet.set_column('H:H', 36)

        work_order_sheet.set_column('I:I', 18)
        work_order_sheet.set_column('J:J', 28)

        work_order_sheet.set_column('K:K', 20)
        work_order_sheet.set_column('L:L', 20)
        work_order_sheet.set_column('M:M', 25)

        work_order_sheet.set_column('N:N', 20)
        work_order_sheet.set_column('O:O', 13)
        work_order_sheet.set_column('P:P', 13)
        work_order_sheet.set_column('Q:Q', 13)
        work_order_sheet.set_column('R:R', 13)
        work_order_sheet.set_column('S:S', 13)
        work_order_sheet.set_column('T:T', 17)
        work_order_sheet.set_column('U:U', 15)
        work_order_sheet.set_column('V:V', 13)
        work_order_sheet.set_column('W:W', 20)

        work_order_sheet.write(7, 0, 'Work Order', design_formats['heading_format_2'])
        work_order_sheet.write(7, 1, 'Region', design_formats['heading_format_2'])
        work_order_sheet.write(7, 2, 'Sales Person', design_formats['heading_format_2'])
        work_order_sheet.write(7, 3, 'WorkOrder Amount', design_formats['heading_format_2'])
        work_order_sheet.write(7, 4, 'Customer Amount', design_formats['heading_format_2'])
        work_order_sheet.write(7, 5, 'Vendor Bill Amount', design_formats['heading_format_2'])
        work_order_sheet.write(7, 6, 'Margin Amount', design_formats['heading_format_2'])
        work_order_sheet.write(7, 7, 'Margin%', design_formats['heading_format_2'])

        wo_row = 8
        wo_col = 0

        trip_sheet = workbook.add_worksheet("FTL Trip Details")

        trip_sheet.merge_range(1, 5, 2, 6, 'FTL Trip Details', design_formats['heading_format'])

        trip_sheet.set_column('A:A', 13)
        trip_sheet.set_column('B:B', 13)

        trip_sheet.set_column('C:C', 25)
        trip_sheet.set_column('D:D', 17)
        trip_sheet.set_column('E:E', 15)
        trip_sheet.set_column('F:F', 20)
        trip_sheet.set_column('G:G', 36)
        trip_sheet.set_column('H:H', 36)

        trip_sheet.set_column('I:I', 18)
        trip_sheet.set_column('J:J', 28)

        trip_sheet.set_column('K:K', 20)
        trip_sheet.set_column('L:L', 20)
        trip_sheet.set_column('M:M', 25)

        trip_sheet.set_column('N:N', 20)
        trip_sheet.set_column('O:O', 13)
        trip_sheet.set_column('P:P', 13)
        trip_sheet.set_column('Q:Q', 13)
        trip_sheet.set_column('R:R', 13)
        trip_sheet.set_column('S:S', 13)
        trip_sheet.set_column('T:T', 17)
        trip_sheet.set_column('U:U', 15)
        trip_sheet.set_column('V:V', 13)
        trip_sheet.set_column('W:W', 20)

        trip_sheet.write(7, 0, 'Work Order', design_formats['heading_format_2'])
        trip_sheet.write(7, 1, 'Req No', design_formats['heading_format_2'])
        # trip_sheet.write(7, 2, 'Trip No', design_formats['heading_format_2'])
        trip_sheet.write(7, 2, 'Region', design_formats['heading_format_2'])
        trip_sheet.write(7, 3, 'Sales Person', design_formats['heading_format_2'])
        trip_sheet.write(7, 4, 'Customer', design_formats['heading_format_2'])
        trip_sheet.write(7, 5, 'Vendor', design_formats['heading_format_2'])
        trip_sheet.write(7, 6, 'Vehicle No', design_formats['heading_format_2'])
        trip_sheet.write(7, 7, 'Vehicle Model', design_formats['heading_format_2'])
        trip_sheet.write(7, 8, 'Vehicle Type', design_formats['heading_format_2'])
        trip_sheet.write(7, 9, 'Source', design_formats['heading_format_2'])
        trip_sheet.write(7, 10, 'Destination', design_formats['heading_format_2'])
        trip_sheet.write(7, 11, 'Start Date', design_formats['heading_format_2'])
        trip_sheet.write(7, 12, 'End Date', design_formats['heading_format_2'])
        trip_sheet.write(7, 13, 'Tonnage', design_formats['heading_format_2'])
        trip_sheet.write(7, 14, 'Total Km', design_formats['heading_format_2'])
        trip_sheet.write(7, 15, 'State', design_formats['heading_format_2'])
        trip_sheet.write(7, 16, 'Amount', design_formats['heading_format_2'])

        trip_row = 8
        trip_col = 0

        domain = [('customer_id', '=', active_model.customer_id.id)]

        if active_model.work_order_id:
            domain.append(('id', '=', active_model.work_order_id.id))
        work_orders = self.env['work.order'].search(domain)

        if work_orders:
            for wo in work_orders:
                # customer_amount = sum(trip_line.amount for trip in wo.trip_ids for trip_line in trip.trip_line_ids)
                trip_domain = [('work_order_id', '=', wo.id), ('state', '=', 'completed')]

                if not active_model.vendor_id:
                    vendor_bills = wo.bill_move_ids.filtered(lambda bill: bill.move_type in ["in_invoice"])
                    vendor_amount = sum(vendor_bills.mapped('amount_total'))
                else:
                    trip_domain.append(('vendor_id', '=', active_model.vendor_id.id))
                    vendor_bills = wo.bill_move_ids.filtered(lambda bill: bill.partner_id.id == active_model.vendor_id.id and bill.move_type in ["in_invoice"])
                    vendor_amount = sum(vendor_bills.mapped('amount_total'))
                trips = self.env['batch.trip.ftl'].search(trip_domain)
                if trips:
                    customer_amount = sum(trip.total_amount for trip in trips)
                    margin_amount = customer_amount - vendor_amount
                    if margin_amount != 0:
                        margin_percentage = round((margin_amount / customer_amount) * 100, 2)
                    else:
                        margin_percentage = 0
                    work_order_sheet.write(wo_row, wo_col, wo.name or '',
                                           design_formats['normal_format_central_border'])
                    work_order_sheet.write(wo_row, wo_col + 1, wo.region_id.name or '',
                                           design_formats['normal_format_central_border'])
                    work_order_sheet.write(wo_row, wo_col + 2, wo.sales_person_id.name or '',
                                           design_formats['normal_format_central_border'])
                    work_order_sheet.write(wo_row, wo_col + 3, wo.total_amount or 0.00,
                                           design_formats['normal_format_central_border'])
                    work_order_sheet.write(wo_row, wo_col + 4, customer_amount or 0.00,
                                           design_formats['normal_format_central_border'])
                    work_order_sheet.write(wo_row, wo_col + 5, vendor_amount or 0.00,
                                           design_formats['normal_format_central_border'])
                    work_order_sheet.write(wo_row, wo_col + 6, margin_amount or 0.00,
                                           design_formats['normal_format_central_border'])
                    work_order_sheet.write(wo_row, wo_col + 7, f"{margin_percentage or 0.00}%",
                                           design_formats['normal_format_central_border'])

                    for trip in trips:
                        trip_sheet.write(trip_row, trip_col, wo.name or '',
                                         design_formats['normal_format_central_border'])
                        trip_sheet.write(trip_row, trip_col + 1, trip.name or '',
                                         design_formats['normal_format_central_border'])
                        # trip_sheet.write(trip_row, trip_col + 2, trip_line.trip_no or '',
                        #                  design_formats['normal_format_central_border'])
                        trip_sheet.write(trip_row, trip_col + 2, trip.region_id.name or '',
                                         design_formats['normal_format_central_border'])
                        trip_sheet.write(trip_row, trip_col + 3, trip.sales_person_id.name or '',
                                         design_formats['normal_format_central_border'])
                        trip_sheet.write(trip_row, trip_col + 4, trip.customer_id.name or '',
                                         design_formats['normal_format_central_border'])
                        trip_sheet.write(trip_row, trip_col + 5, trip.vendor_id.name or '',
                                         design_formats['normal_format_central_border'])
                        trip_sheet.write(trip_row, trip_col + 6, trip.vehicle_id.vehicle_no or '',
                                         design_formats['normal_format_central_border'])
                        trip_sheet.write(trip_row, trip_col + 7, trip.vehicle_model_id.name or '',
                                         design_formats['normal_format_central_border'])
                        trip_sheet.write(trip_row, trip_col + 8, trip.vehicle_type_id.name or '',
                                         design_formats['normal_format_central_border'])
                        trip_sheet.write(trip_row, trip_col + 9, trip.source_id.name or '',
                                         design_formats['normal_format_central_border'])
                        trip_sheet.write(trip_row, trip_col + 10, trip.destination_id.name or '',
                                         design_formats['normal_format_central_border'])
                        trip_sheet.write(trip_row, trip_col + 11, trip.start_date or '',
                                         design_formats['date_format_border'])
                        trip_sheet.write(trip_row, trip_col + 12, trip.end_date or '',
                                         design_formats['date_format_border'])
                        trip_sheet.write(trip_row, trip_col + 13, trip.tonnage or '',
                                         design_formats['normal_format_central_border'])
                        trip_sheet.write(trip_row, trip_col + 14, trip.total_km or 0.00,
                                         design_formats['normal_format_central_border'])
                        trip_sheet.write(trip_row, trip_col + 15,
                                         dict(trip._fields['state'].selection).get(
                                             trip.state) or '',
                                         design_formats['normal_format_central_border'])

                        trip_sheet.write(trip_row, trip_col + 16, trip.total_amount or 0.00,
                                         design_formats['normal_format_central_border'])
                        trip_row = trip_row + 1
                    wo_row = wo_row + 1
