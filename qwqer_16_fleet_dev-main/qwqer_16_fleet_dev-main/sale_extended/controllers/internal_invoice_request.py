import json
from datetime import datetime
import logging

import pytz
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError


class InternalInvoiceRequest(http.Controller):

    @http.route(['/internal/invoice/request/'], type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def internal_invoice_request(self, api_raw_log=None, **kwargs):
        _logger.info("Internal Invoice Request API : Request Received, Processing ... Time : %s", fields.datetime.now())

        if not kwargs:
            return self._handle_error(api_raw_log, "No Data Received or Incorrect Data Format", 500)

        params = {k: (False if v is None else v) for k, v in kwargs.items()}
        order_id = params.get('order_id')
        if not order_id:
            return self._handle_error(api_raw_log, "Mandatory Parameter Order ID Missing", 500)

        sale_order = request.env['sale.order'].search([('order_id', '=', order_id)], limit=1)

        invoice_id = False
        invoice_link = ''

        if sale_order:
            if sale_order.invoice_status == "invoiced":
                if sale_order.invoice_ids:
                    invoice_id = \
                    sale_order.invoice_ids.filtered(lambda r: r.move_type == 'out_invoice').sorted(key='id',
                                                                                                   reverse=True)[
                        0] or False
                    invoice_link = request.httprequest.host_url + \
                                   invoice_id.get_portal_url() + \
                                   '&report_type=pdf&download=true'
                    if invoice_link:
                        pass

                estimated_time_time = "%02d:%02d:%02d" % (
                int(sale_order.estimated_time), ((sale_order.estimated_time * 60) % 60),
                ((sale_order.estimated_time * 3600) % 60))
                time_to_accept_time = "%02d:%02d:%02d" % (
                int(sale_order.time_to_accept), ((sale_order.time_to_accept * 60) % 60),
                ((sale_order.time_to_accept * 3600) % 60))
                time_to_pickup_time = "%02d:%02d:%02d" % (
                int(sale_order.time_to_pickup), ((sale_order.time_to_pickup * 60) % 60),
                ((sale_order.time_to_pickup * 3600) % 60))
                time_to_deliver_time = "%02d:%02d:%02d" % (
                int(sale_order.time_to_deliver), ((sale_order.time_to_deliver * 60) % 60),
                ((sale_order.time_to_deliver * 3600) % 60))
                overall_order_time_time = "%02d:%02d:%02d" % (
                int(sale_order.overall_order_time), ((sale_order.overall_order_time * 60) % 60),
                ((sale_order.overall_order_time * 3600) % 60))
                local = pytz.timezone(request.env.user.tz or pytz.utc)
                tz_order_picked_up_date = ""
                tz_order_delivered_date = ""
                tz_date_order = ""
                tz_accepted_date = ""
                ack_date = ""
                irn_no = ""
                ack_no = ""
                if sale_order.order_accepted_date:
                    tz_accepted_date = datetime.strftime(local.fromutc(sale_order.order_accepted_date),
                                                         "%d/%m/%Y %H:%M:%S")
                if sale_order.order_picked_up_date:
                    tz_order_picked_up_date = datetime.strftime(local.fromutc(sale_order.order_picked_up_date),
                                                                "%d/%m/%Y %H:%M:%S")
                if sale_order.order_delivered_date:
                    tz_order_delivered_date = datetime.strftime(local.fromutc(sale_order.order_delivered_date),
                                                                "%d/%m/%Y %H:%M:%S")
                if sale_order.date_order:
                    tz_date_order = datetime.strftime(local.fromutc(sale_order.date_order), "%d/%m/%Y %H:%M:%S")
                if invoice_id and invoice_id.einvoice_generated:
                    if invoice_id.ack_date:
                        ack_date = datetime.strftime(local.fromutc(invoice_id.ack_date), "%d/%m/%Y %H:%M:%S")
                    else:
                        ack_date = datetime.strftime(local.fromutc(invoice_id.einvocie_details_ids.ack_date),
                                                     "%d/%m/%Y %H:%M:%S")
                    if invoice_id.irn:
                        irn_no = invoice_id.irn
                    else:
                        irn_no = invoice_id.einvocie_details_ids.irn or False,
                    if invoice_id.ack_no:
                        ack_no = invoice_id.ack_no
                    else:
                        ack_no = invoice_id.einvocie_details_ids.ack_no

                if sale_order.accept_sla == 't':
                    accept_sla = '1'
                else:
                    accept_sla = '0'

                if sale_order.pickup_sla == 't':
                    pickup_sla = '1'
                else:
                    pickup_sla = '0'
                order_values = json.dumps({
                    'status': "SUCCESS",
                    'status_code': '200',
                    'msg': 'Order Found',
                    'customer_name': sale_order.partner_id.name,
                    'customer_type': sale_order.partner_id.customer_type if sale_order.partner_id.customer_type else None,
                    "order_id": sale_order.order_id if sale_order.order_id else None,
                    "region": sale_order.region_id.region_code if sale_order.region_id else None,
                    "order_status": sale_order.order_status_id.code if sale_order.order_status_id.code else None,
                    "order_date_time": tz_date_order if tz_date_order else None,
                    "order_amount": sale_order.order_amount if sale_order.order_amount else None,
                    "discount_amount": sale_order.discount_amount if sale_order.discount_amount else None,
                    "order_source": sale_order.order_source_sel if sale_order.order_source_sel else None,
                    "cancellation_comments": sale_order.cancellation_comments if sale_order.cancellation_comments else None,
                    "promo_code": sale_order.promo_code if sale_order.promo_code else None,
                    "merchant_order_amount": sale_order.merchant_order_amount if sale_order.merchant_order_amount else None,
                    "payment_id": sale_order.payment_id if sale_order.payment_id else None,
                    "payment_status": sale_order.payment_status if sale_order.payment_status else None,
                    "payment_mode": sale_order.payment_mode_id.code if sale_order.payment_mode_id.code else None,
                    "estimated_distance": sale_order.estimated_distance if sale_order.estimated_distance else None,
                    "estimated_time": estimated_time_time if estimated_time_time else None,
                    "pickup_distance": sale_order.pickup_distance if sale_order.pickup_distance else None,
                    "deliver_distance": sale_order.deliver_distance if sale_order.deliver_distance else None,
                    "weight": sale_order.weight if sale_order.weight else None,
                    "item_type": sale_order.item_type if sale_order.item_type else None,
                    "description": sale_order.description if sale_order.description else None,
                    "from_name": sale_order.from_name if sale_order.from_name else None,
                    "from_phone_no": sale_order.from_phone_no if sale_order.from_phone_no else None,
                    "from_address": sale_order.from_address if sale_order.from_address else None,
                    "sender_locality": sale_order.sender_locality if sale_order.sender_locality else None,
                    "from_postal_code": sale_order.from_postal_code if sale_order.from_postal_code else None,
                    "to_name": sale_order.to_name if sale_order.to_name else None,
                    "to_phone_no": sale_order.to_phone_no if sale_order.to_phone_no else None,
                    "to_address": sale_order.to_address if sale_order.to_address else None,
                    "receiver_locality": sale_order.receiver_locality if sale_order.receiver_locality else None,
                    "to_postal_code": sale_order.to_postal_code if sale_order.to_postal_code else None,
                    "driver_id": sale_order.driver_id.driver_uid if sale_order.driver_id.driver_uid else None,
                    "driver_name": sale_order.driver_name if sale_order.driver_name else None,
                    "driver_phone": sale_order.driver_phone if sale_order.driver_phone else None,
                    "driver_rating": sale_order.driver_rating if sale_order.driver_rating else None,
                    "driver_comment": sale_order.driver_comment if sale_order.driver_comment else None,
                    "customer_rating": sale_order.customer_ratin if sale_order.customer_rating else None,
                    "customer_feedback": sale_order.customer_feedback if sale_order.customer_feedback else None,
                    "customer_comment": sale_order.customer_comment if sale_order.customer_comment else None,
                    "order_accepted_date_time": tz_accepted_date,
                    "order_picked_up_date_time": tz_order_picked_up_date,
                    "order_delivered_date_time": tz_order_delivered_date,
                    "time_to_accept": time_to_accept_time,
                    "time_to_pickup": time_to_pickup_time,
                    "time_to_deliver": time_to_deliver_time,
                    "overall_order_time": overall_order_time_time,
                    "pricing_plan": sale_order.pricing_plan,
                    "accept_sla": accept_sla,
                    "pickup_sla": pickup_sla,
                    "invoice_amount": invoice_id and invoice_id.amount_total or 0.00,
                    "invoice_id": invoice_id and invoice_id.id or False,
                    "invoice_url": invoice_link,
                    "is_einvoice_generated": invoice_id and invoice_id.einvoice_generated,
                    "irn_no": irn_no or False,
                    "ack_no": ack_no or False,
                    "ack_date": ack_date or False
                })
                api_raw_log.update({"response": order_values,
                                    'response_date': fields.Datetime.now(),
                                    'name': "Internal Invoice Request",
                                    'key': order_id and str(order_id),
                                    'status': "SUCCESS"})
                return order_values
            else:
                status = "REJECTED"
                status_code = 500
                response = json.dumps({
                    'status': status,
                    'status_code': status_code,
                    'msg': "The order has not been invoiced",
                })
                self._handle_error(api_raw_log, "The order has not been invoiced", 500)
                return response
        else:
            status = "REJECTED"
            status_code = 500
            response = json.dumps({
                'status': status,
                'status_code': status_code,
                'msg': "Order Not Found",
            })
            self._handle_error(api_raw_log, "Order Not Found", 500)
            return response



    def _handle_error(self, api_raw_log, message, status_code):
        error = APIError(status="REJECTED", status_code=status_code, message=message)
        api_raw_log.update(
            {'response': message, 'response_date': datetime.now(), 'name': "Internal Invoice Request",
             'status': "REJECTED"})
        return error.to_response(api_raw_log=api_raw_log, name="Internal Invoice Request")
