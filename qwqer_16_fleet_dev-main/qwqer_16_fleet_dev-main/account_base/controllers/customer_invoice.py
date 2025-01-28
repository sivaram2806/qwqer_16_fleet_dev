# coding=utf-8
import logging
from dataclasses import fields
from odoo import http


logger = logging.getLogger(__name__)

from odoo import fields
import json
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError
from odoo.addons.account.models.account_move import PAYMENT_STATE_SELECTION
import logging

_logger = logging.getLogger(__name__)

class InvoiceRoute(http.Controller):

    @http.route('/customer_invoice/request', type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def upload_document(self, api_raw_log=None, **kwargs):
        """API to get customer invoices by customer id"""
        customer_id = kwargs.get('customer_id', False)
        try:
            if customer_id:
                invoices = request.env["account.move"].search(
                    [('partner_id.customer_ref_key', '=', customer_id), ('move_type', 'in', ('out_invoice', 'out_refund')),
                     ('state', '=', 'posted'), '|', ('payment_mode_id', '=', False),
                     ('payment_mode_id.is_credit_payment', '=', True)], order='date desc, name desc, id desc')

                invoice_list = []
                for invoice in invoices:
                    invoice_link = request.httprequest.host_url + \
                                   invoice.get_portal_url() + \
                                   '&report_type=pdf&download=true'
                    invoice_list.append({'inv_no': invoice.name,
                                         'inv_date': str(invoice.invoice_date),
                                        'due_date': str(invoice.invoice_date_due),
                                        'invoice_status': invoice.state,
                                        'payment_status': invoice.payment_state,
                                        'total_amt': round(invoice.amount_total, 2),
                                        'amount_due': round(invoice.amount_residual, 2),
                                        'invoice_link': invoice_link
                    })
                response = ({'status': "SUCCESS",
                             'status_code': 200,
                             'message': "Successfully fetched data",
                             'invoice_details': invoice_list
                    })
                api_raw_log.update({"response": json.dumps(response),
                                    'response_date': fields.Datetime.now(),
                                    'name': "Customer Invoice Listing",
                                    'key': customer_id and str(customer_id),
                                    'status': response['status']})
                return json.dumps(response)
            else:
                _logger.info("Service API : No Data Received or Incorrect Data Format!")
                raise APIError(status="REJECTED", status_code=500,
                               message="No Data Received or Incorrect Data Format!")

        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name="Customer Invoice Listing")
        except Exception as e:
            _logger.error(f"Service API : No Data Received or Incorrect Data Format!{str(e)}")
            error = APIError(status="error", status_code=500,
                             message="An unexpected error occurred. Please try again later")
            response = error.to_response(api_raw_log=api_raw_log, name="Customer Invoice Listing")
            return response
