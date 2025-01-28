# -*- coding: utf-8 -*-

import logging
import json

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CashfreePaymentApiController(http.Controller):

    @http.route(['/cashfree_payment/request/'], type='json', auth='public', methods=['POST'], csrf=False)
    def service_post(self, **post):
        # Fetching API credentials
        _logger.info("Cashfree Payin API : Cashfree Request Received, Processing ......")

        # Initial status and response handling
        status_code = 500
        status = "REJECTED"
        response = request.httprequest.data

        try:
            # Decode the response and convert it into a dictionary
            response_decoded = json.loads(response.decode('utf-8'))
            _logger.info("Cashfree Payin API : Response Decoded !!")

            # Verify if the response contains necessary data
            data = response_decoded.get('data', {})
            event_time = response_decoded.get('event_time')

            if not data:
                _logger.info("Cashfree Payin API : No Data Received or Incorrect Data Format!")
                return {
                    'status': status,
                    'status_code': status_code,
                    'msg': "No Data Received or Incorrect Data Format!"
                }

            # Ensure 'transaction_id' is present
            if 'transaction_id' not in data.get('order', {}):
                _logger.info('Cashfree Payin API : Transaction Id Not Available Returning')
                return {
                    'status': status,
                    'status_code': 400,
                    'msg': "An Error Occurred - transaction_id Not Available",
                }

            # Prepare the log values
            log_vals = {'response_json': response_decoded}

            # Populate log_vals with relevant data if available
            log_vals.update({
                'payment_status': data.get('link_status'),
                'link_id': data.get('link_id'),
                'currency_id': request.env['res.currency'].search([('name', '=', data.get('link_currency'))], limit=1).id,
                'amount_paid': data.get('link_amount_paid'),
                'event_time': event_time,
                'invoice_id': int(data.get('link_notes', {}).get('invoice', 0)),
                'purpose': data.get('link_purpose'),
                'customer_phone': data.get('customer_details', {}).get('customer_phone'),
                'cf_link_id': str(data.get('cf_link_id')),
                'order_id_num': data.get('order', {}).get('order_id'),
                'transaction_id': data.get('order', {}).get('transaction_id'),
                'transaction_status': str(data.get('order', {}).get('transaction_status'))
            })

            # Create the record and log the response
            rec = request.env["cashfree.payin"].sudo().create(log_vals)
            _logger.info("Cashfree Payin API : Response for Cashfree Payment %s", str(rec))
            return response

        except Exception as e:
            _logger.error("Cashfree Payin API : An error occurred - %s", str(e))
            return {
                'status': status,
                'status_code': status_code,
                'msg': "An Error Occurred: " + str(e),
            }
