from odoo import models, fields
import logging
import datetime
from datetime import datetime
import pytz

_logger = logging.getLogger('__name__')


class SaleOrderExcelReport(models.AbstractModel):
    _name = "report.kpi_reports.sale_orders_report_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, obj):
        cell_text_format = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 10})
        format3 = workbook.add_format({'align': 'left', 'bold': False, 'font_size': 10})
        head = workbook.add_format({'align': 'center', 'size': 12, 'bold': True})
        head2 = workbook.add_format({'align': 'center', 'size': 10, 'bold': True})
        head3 = workbook.add_format({'align': 'center', 'font_size': 10, 'bold': True, 'bg_color': '#808080'})
        worksheet = workbook.add_worksheet('saleorder.xlsx')
        company_name = self.env.user.company_id.name
        company_street = self.env.user.company_id.street if self.env.user.company_id.street else ''
        company_street2 = self.env.user.company_id.street2 if self.env.user.company_id.street2 else ''
        company_city = self.env.user.company_id.city if self.env.user.company_id.city else ''
        company_zip = self.env.user.company_id.zip if self.env.user.company_id.zip else ''
        company_addr = str(company_street + ' , ' + ' ' + company_street2 + '  ' + company_city + '  ' + company_zip)
        company_mob = self.env.user.company_id.phone if self.env.user.company_id.phone else ''
        company_email = self.env.user.company_id.email if self.env.user.company_id.email else ''
        company_website = self.env.user.company_id.website if self.env.user.company_id.website else ''
        if company_mob and company_email and company_website:
            company_addr1 = 'Ph:' + company_mob + ',' + ' ' + 'Email:' + company_email + ',' + ' ' + 'Website:' + company_website
        else:
            company_addr1 = ''
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 16)
        worksheet.set_column('C:C', 12)
        worksheet.set_column('D:D', 12)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 13)
        worksheet.set_column('H:H', 18)
        worksheet.set_column('I:I', 14)
        worksheet.set_column('J:J', 14)
        worksheet.set_column('K:K', 14)
        worksheet.set_column('L:L', 14)
        worksheet.set_column('M:M', 14)
        worksheet.set_column('N:N', 14)
        worksheet.set_column('O:O', 14)
        worksheet.set_column('P:P', 14)
        worksheet.set_column('Q:Q', 16)
        worksheet.set_column('R:R', 14)
        worksheet.set_column('S:S', 14)
        worksheet.set_column('T:T', 14)
        worksheet.set_column('U:U', 14)
        worksheet.set_column('V:V', 14)
        worksheet.set_column('W:W', 14)
        worksheet.set_column('X:X', 14)
        worksheet.set_column('Y:Y', 14)
        worksheet.set_column('Z:Z', 14)
        worksheet.set_column('AA:AA', 14)
        worksheet.set_column('AB:AB', 14)
        worksheet.set_column('AC:AC', 14)
        worksheet.set_column('AD:AD', 14)
        worksheet.set_column('AE:AE', 14)
        worksheet.set_column('AF:AF', 14)
        worksheet.set_column('AG:AG', 14)
        worksheet.set_column('AH:AH', 14)
        worksheet.set_column('AI:AI', 14)
        worksheet.set_column('AJ:AJ', 14)
        worksheet.set_column('AK:AK', 14)
        worksheet.set_column('AL:AL', 14)
        worksheet.set_column('AM:AM', 14)
        worksheet.set_column('AN:AN', 14)
        worksheet.set_column('AO:AO', 14)
        worksheet.set_column('AP:AP', 14)
        worksheet.set_column('AQ:AQ', 14)
        worksheet.set_column('AR:AR', 14)
        worksheet.set_column('AS:AS', 14)
        worksheet.set_column('AT:AT', 14)
        worksheet.set_column('AU:AU', 14)
        worksheet.set_column('AV:AV', 14)
        worksheet.set_column('AW:AW', 14)
        worksheet.set_column('AX:AX', 14)
        worksheet.set_column('AY:AY', 14)
        worksheet.set_column('AZ:AZ', 14)
        worksheet.set_column('BA:BA', 14)

        worksheet.merge_range('A1:I2', company_name, head)
        worksheet.merge_range('A3:I4', company_addr, head2)
        worksheet.merge_range('A5:I6', company_addr1, head2)

        row = 7
        column = 0

        worksheet.merge_range('D7:F7', 'Sale Order Report', head)
        row += 2
        from_date = fields.Date.from_string(data['from_date']).strftime('%d/%m/%Y')
        to_date = fields.Date.from_string(data['to_date']).strftime('%d/%m/%Y')

        worksheet.write(row, column, 'From Date', cell_text_format)
        worksheet.write(row, column + 1, from_date, cell_text_format)
        worksheet.write(row, column + 3, 'To Date', cell_text_format)
        worksheet.write(row, column + 4, to_date, cell_text_format)

        row += 2
        worksheet.write(row, column, 'Sl. No', cell_text_format)
        worksheet.write(row, column + 1, 'Customer Name', cell_text_format)
        worksheet.write(row, column + 2, 'Customer Type', cell_text_format)
        worksheet.write(row, column + 3, 'Order ID', cell_text_format)
        worksheet.write(row, column + 4, 'Region', cell_text_format)
        worksheet.write(row, column + 5, 'Order Status', cell_text_format)
        worksheet.write(row, column + 6, 'Order Date Time', cell_text_format)
        worksheet.write(row, column + 7, 'Order Amount', cell_text_format)
        worksheet.write(row, column + 8, 'Discount Amount', cell_text_format)
        worksheet.write(row, column + 9, 'Order Source', cell_text_format)
        worksheet.write(row, column + 10, 'Cancellation Comments', cell_text_format)
        worksheet.write(row, column + 11, 'Promo Code', cell_text_format)
        worksheet.write(row, column + 12, 'Merchant Order Amount', cell_text_format)
        worksheet.write(row, column + 13, 'Payment ID', cell_text_format)
        worksheet.write(row, column + 14, 'Payment Status', cell_text_format)
        worksheet.write(row, column + 15, 'Payment Mode', cell_text_format)
        worksheet.write(row, column + 16, 'Estimated Distance', cell_text_format)
        worksheet.write(row, column + 17, 'Estimated Time', cell_text_format)
        worksheet.write(row, column + 18, 'Pickup Distance', cell_text_format)
        worksheet.write(row, column + 19, 'Deliver Distance', cell_text_format)
        worksheet.write(row, column + 20, 'Weight', cell_text_format)
        worksheet.write(row, column + 21, 'Item Type', cell_text_format)
        worksheet.write(row, column + 22, 'Description', cell_text_format)
        worksheet.write(row, column + 23, 'From Name', cell_text_format)
        worksheet.write(row, column + 24, 'From Phone No', cell_text_format)
        worksheet.write(row, column + 25, 'From Address', cell_text_format)
        worksheet.write(row, column + 26, 'Sender Locality', cell_text_format)
        worksheet.write(row, column + 27, 'From Postal Code', cell_text_format)
        worksheet.write(row, column + 28, 'To Name', cell_text_format)
        worksheet.write(row, column + 29, 'To Phone No', cell_text_format)
        worksheet.write(row, column + 30, 'To Address', cell_text_format)
        worksheet.write(row, column + 31, 'Receiver Locality', cell_text_format)
        worksheet.write(row, column + 32, 'To Postal Code', cell_text_format)
        worksheet.write(row, column + 33, 'Driver ID', cell_text_format)
        worksheet.write(row, column + 34, 'Driver Name', cell_text_format)
        worksheet.write(row, column + 35, 'Driver Phone', cell_text_format)
        worksheet.write(row, column + 36, 'Driver Rating', cell_text_format)
        worksheet.write(row, column + 37, 'Driver Comment', cell_text_format)
        worksheet.write(row, column + 38, 'Customer Rating', cell_text_format)
        worksheet.write(row, column + 39, 'Customer Feedback', cell_text_format)
        worksheet.write(row, column + 40, 'Customer Comment', cell_text_format)
        worksheet.write(row, column + 41, 'Order Accepted Date Time', cell_text_format)
        worksheet.write(row, column + 42, 'Order Picked Up Date Time', cell_text_format)
        worksheet.write(row, column + 43, 'Order Delivered Date Time', cell_text_format)
        worksheet.write(row, column + 44, 'Time to accept', cell_text_format)
        worksheet.write(row, column + 45, 'Time to Pickup', cell_text_format)
        worksheet.write(row, column + 46, 'Time to Deliver', cell_text_format)
        worksheet.write(row, column + 47, 'OrderAll Order Time', cell_text_format)
        worksheet.write(row, column + 48, 'Pricing Plan', cell_text_format)
        worksheet.write(row, column + 49, 'Accept SLA', cell_text_format)
        worksheet.write(row, column + 50, 'Pickup SLA', cell_text_format)
        worksheet.write(row, column + 51, 'Invoice Amount', cell_text_format)
        worksheet.write(row, column + 52, 'Invoice ID', cell_text_format)

        order_list = []
        domain = []
        local = pytz.timezone(self.env.user.tz or pytz.utc)
        from_date = data['from_date'] + ' ' + '00:00:00'
        _logger.info("From date %s", from_date)
        from_naive_schedule = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S")
        from_local_dt_schedule = local.localize(from_naive_schedule, is_dst=None)
        utc_from_date = from_local_dt_schedule.astimezone(pytz.utc)
        _logger.info("UTC From date %s", utc_from_date)

        to_date = data['to_date'] + ' ' + '23:59:59'
        _logger.info("To date %s", to_date)
        to_naive_schedule = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S")
        to_local_dt_schedule = local.localize(to_naive_schedule, is_dst=None)
        utc_to_date = to_local_dt_schedule.astimezone(pytz.utc)
        _logger.info("UTC To date %s", utc_to_date)

        if data['from_date']:
            domain.append(('date_order', '>=', utc_from_date))
        if data['to_date']:
            domain.append(('date_order', '<=', utc_to_date))
        if data['partner_ids']:
            domain.append(('partner_id', '=', data['partner_ids']))
        domain.append(('state', '=', 'sale'))
        orders = self.env['sale.order'].search(domain)
        for order in orders:
            estimated_time_time = "%02d:%02d:%02d" % (int(order.estimated_time), \
                                                      ((order.estimated_time * 60) % 60), \
                                                      ((order.estimated_time * 3600) % 60))
            time_to_accept_time = "%02d:%02d:%02d" % (int(order.time_to_accept), \
                                                      ((order.time_to_accept * 60) % 60), \
                                                      ((order.time_to_accept * 3600) % 60))
            time_to_pickup_time = "%02d:%02d:%02d" % (int(order.time_to_pickup), \
                                                      ((order.time_to_pickup * 60) % 60), \
                                                      ((order.time_to_pickup * 3600) % 60))
            time_to_deliver_time = "%02d:%02d:%02d" % (int(order.time_to_deliver), \
                                                       ((order.time_to_deliver * 60) % 60), \
                                                       ((order.time_to_deliver * 3600) % 60))
            overall_order_time_time = "%02d:%02d:%02d" % (int(order.overall_order_time), \
                                                          ((order.overall_order_time * 60) % 60), \
                                                          ((order.overall_order_time * 3600) % 60))

            local = pytz.timezone(self.env.user.tz or pytz.utc)
            _logger.info("Service API : Local %s ", local)

            tz_order_picked_up_date = ''
            tz_accepted_date = ''
            tz_order_delivered_date = ''

            if order.order_accepted_date:
                tz_accepted_date = datetime.strftime(local.fromutc(order.order_accepted_date), "%d/%m/%Y %H:%M:%S")
            if order.order_picked_up_date:
                tz_order_picked_up_date = datetime.strftime(local.fromutc(order.order_picked_up_date),
                                                            "%d/%m/%Y %H:%M:%S")
            if order.order_delivered_date:
                tz_order_delivered_date = datetime.strftime(local.fromutc(order.order_delivered_date),
                                                            "%d/%m/%Y %H:%M:%S")
            tz_date_order = datetime.strftime(local.fromutc(order.date_order), "%d/%m/%Y %H:%M:%S")

            accept_sla = ''
            pickup_sla = ''

            if order.accept_sla == 't':
                accept_sla = '1'
            else:
                accept_sla = '0'

            if order.pickup_sla == 't':
                pickup_sla = '1'
            else:
                pickup_sla = '0'

            order_dict = {
                'customer_name': order.partner_id.name,
                'customer_type': order.partner_id.customer_type if order.partner_id.customer_type else None,
                "order_id": order.order_id,
                "region": order.region_id.name if order.region_id else None,
                "order_status": order.order_status_id.code if order.order_status_id.code else None,
                "order_date_time": tz_date_order,
                "order_amount": order.order_amount if order.order_amount else None,
                "discount_amount": order.discount_amount if order.discount_amount else None,
                "order_source": order.order_source_sel if order.order_source_sel else None,
                "cancellation_comments": order.cancellation_comments if order.cancellation_comments else None,
                "promo_code": order.promo_code if order.promo_code else None,
                "merchant_order_amount": order.merchant_order_amount if order.merchant_order_amount else None,
                "payment_id": order.payment_id if order.payment_id else None,
                "payment_status": order.payment_status if order.payment_status else None,
                "payment_mode": order.payment_mode_id.code if order.payment_mode_id.code else None,
                "estimated_distance": order.estimated_distance if order.estimated_distance else None,
                "estimated_time": estimated_time_time if estimated_time_time else None,
                "pickup_distance": order.pickup_distance if order.pickup_distance else None,
                "deliver_distance": order.deliver_distance if order.deliver_distance else None,
                "weight": order.weight if order.weight else None,
                "item_type": order.item_type if order.item_type else None,
                "description": order.description if order.description else None,
                "from_name": order.from_name if order.from_name else None,
                "from_phone_no": order.from_phone_no if order.from_phone_no else None,
                "from_address": order.from_address if order.from_address else None,
                "sender_locality": order.sender_locality if order.sender_locality else None,
                "from_postal_code": order.from_postal_code if order.from_postal_code else None,
                "to_name": order.to_name if order.to_name else None,
                "to_phone_no": order.to_phone_no if order.to_phone_no else None,
                "to_address": order.to_address if order.to_address else None,
                "receiver_locality": order.receiver_locality if order.receiver_locality else None,
                "to_postal_code": order.to_postal_code if order.to_postal_code else None,
                "driver_id": order.driver_id.driver_uid if order.driver_id.driver_uid else None,
                "driver_name": order.driver_name if order.driver_name else None,
                "driver_phone": order.driver_phone if order.driver_phone else None,
                "driver_rating": order.driver_rating if order.driver_rating else None,
                "driver_comment": order.driver_comment if order.driver_comment else None,
                "customer_rating": order.customer_rating if order.customer_rating else None,
                "customer_feedback": order.customer_feedback if order.customer_feedback else None,
                "customer_comment": order.customer_comment if order.customer_comment else None,
                "order_accepted_date_time": tz_accepted_date,
                "order_picked_up_date_time": tz_order_picked_up_date,
                "order_delivered_date_time": tz_order_delivered_date,
                "time_to_accept": time_to_accept_time,
                "time_to_pickup": time_to_pickup_time,
                "time_to_deliver": time_to_deliver_time,
                "overall_order_time": overall_order_time_time,
                "pricing_plan": order.pricing_plan,
                "accept_sla": accept_sla,
                "pickup_sla": pickup_sla,
                "invoice_amount": order.invoice_ids.amount_total if order.invoice_ids else None,
                "invoice_id": order.invoice_ids.id if order.invoice_ids else None,
            }
            order_list.append(order_dict)

        i = 0
        for rec in order_list:
            row += 1
            worksheet.write(row + 1, column, i + 1, format3)
            worksheet.write(row + 1, column + 1, rec['customer_name'], format3)
            worksheet.write(row + 1, column + 2, rec['customer_type'], format3)
            worksheet.write(row + 1, column + 3, rec['order_id'], format3)
            worksheet.write(row + 1, column + 4, rec['region'], format3)
            worksheet.write(row + 1, column + 5, rec['order_status'], format3)
            worksheet.write(row + 1, column + 6, rec['order_date_time'], format3)
            worksheet.write(row + 1, column + 7, rec['order_amount'], format3)
            worksheet.write(row + 1, column + 8, rec['discount_amount'], format3)
            worksheet.write(row + 1, column + 9, rec['order_source'], format3)
            worksheet.write(row + 1, column + 10, rec['cancellation_comments'], format3)
            worksheet.write(row + 1, column + 11, rec['promo_code'], format3)
            worksheet.write(row + 1, column + 12, rec['merchant_order_amount'], format3)
            worksheet.write(row + 1, column + 13, rec['payment_id'], format3)
            worksheet.write(row + 1, column + 14, rec['payment_status'], format3)
            worksheet.write(row + 1, column + 15, rec['payment_mode'], format3)
            worksheet.write(row + 1, column + 16, rec['estimated_distance'], format3)
            worksheet.write(row + 1, column + 17, rec['estimated_time'], format3)
            worksheet.write(row + 1, column + 18, rec['pickup_distance'], format3)
            worksheet.write(row + 1, column + 19, rec['deliver_distance'], format3)
            worksheet.write(row + 1, column + 20, rec['weight'], format3)
            worksheet.write(row + 1, column + 21, rec['item_type'], format3)
            worksheet.write(row + 1, column + 22, rec['description'], format3)
            worksheet.write(row + 1, column + 23, rec['from_name'], format3)
            worksheet.write(row + 1, column + 24, rec['from_phone_no'], format3)
            worksheet.write(row + 1, column + 25, rec['from_address'], format3)
            worksheet.write(row + 1, column + 26, rec['sender_locality'], format3)
            worksheet.write(row + 1, column + 27, rec['from_postal_code'], format3)
            worksheet.write(row + 1, column + 28, rec['to_name'], format3)
            worksheet.write(row + 1, column + 29, rec['to_phone_no'], format3)
            worksheet.write(row + 1, column + 30, rec['to_address'], format3)
            worksheet.write(row + 1, column + 31, rec['receiver_locality'], format3)
            worksheet.write(row + 1, column + 32, rec['to_postal_code'], format3)
            worksheet.write(row + 1, column + 33, rec['driver_id'], format3)
            worksheet.write(row + 1, column + 34, rec['driver_name'], format3)
            worksheet.write(row + 1, column + 35, rec['driver_phone'], format3)
            worksheet.write(row + 1, column + 36, rec['driver_rating'], format3)
            worksheet.write(row + 1, column + 37, rec['driver_comment'], format3)
            worksheet.write(row + 1, column + 38, rec['customer_rating'], format3)
            worksheet.write(row + 1, column + 39, rec['customer_feedback'], format3)
            worksheet.write(row + 1, column + 40, rec['customer_comment'], format3)
            worksheet.write(row + 1, column + 41, rec['order_accepted_date_time'], format3)
            worksheet.write(row + 1, column + 42, rec['order_picked_up_date_time'], format3)
            worksheet.write(row + 1, column + 43, rec['order_delivered_date_time'], format3)
            worksheet.write(row + 1, column + 44, rec['time_to_accept'], format3)
            worksheet.write(row + 1, column + 45, rec['time_to_pickup'], format3)
            worksheet.write(row + 1, column + 46, rec['time_to_deliver'], format3)
            worksheet.write(row + 1, column + 47, rec['overall_order_time'], format3)
            worksheet.write(row + 1, column + 48, rec['pricing_plan'], format3)
            worksheet.write(row + 1, column + 49, rec['accept_sla'], format3)
            worksheet.write(row + 1, column + 50, rec['pickup_sla'], format3)
            worksheet.write(row + 1, column + 51, rec['invoice_amount'], format3)
            worksheet.write(row + 1, column + 52, rec['invoice_id'], format3)
            i += 1
