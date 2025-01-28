import json
from datetime import datetime
import logging

from pytz import timezone, UTC

from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError
from psycopg2.errors import UniqueViolation


class DriverPayInCreationController(http.Controller):
    @http.route(['/internal/driver/request/'], type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def create_driver_payin(self, api_raw_log=None, **kwargs):
        """API to Create driver payin"""
        _logger.info("Received kwargs: %s", kwargs)
        try:
            if not kwargs:
                raise APIError(status="REJECTED", status_code=500,
                               message="No Data Received or Incorrect Data Format!")
            driver_id = kwargs.get('driver_id', False)
            # check driver
            if not driver_id:
                raise APIError(status="REJECTED", status_code=402,
                               message="Driver ID Not Available")
            params = {k: (False if v is None else v) for k, v in kwargs.items()}
            _logger.info("Driver Creation API : Raw Data (JSON) copied")

            if params:
                response = self.create_pay_in(params)
                api_raw_log.update({
                    "response": json.dumps(response),
                    'response_date': fields.Datetime.now(),
                    'name': "Partner Wallet Deduction",
                    'key': driver_id,
                    'status': response['status']
                })
                return json.dumps(response)

        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name="Driver Payin Creation")
        except Exception as e:
            _logger.error(f"Unexpected error: {str(e)}")
            error = APIError(status="error", status_code=500,
                             message="An unexpected error occurred. Please try again later")
            return error.to_response(api_raw_log=api_raw_log, name="Driver Payin Creation")

    def create_pay_in(self, params):
        """
        Create driver pay in details based on provided parameters.
        """
        vals = {}
        driver_id = request.env['hr.employee'].sudo().search(
            [('driver_uid', '=', params['driver_id'])], limit=1)
        if driver_id:
            if not driver_id.related_partner_id:
                raise APIError(status="REJECTED", status_code=402,
                               message="Related partner is missing for the Driver")
        else:
            raise APIError(status="REJECTED", status_code=402,
                           message="Driver ID Not Available")
        vals.update({'employee_id': driver_id.id})
        remit_date = params.get('remit_date', False)
        if remit_date:
            local = timezone(request.env.user.tz or UTC)
            try:
                naive_order_time = datetime.strptime(remit_date, "%Y-%m-%d %H:%M:%S")
                local_dt_remit_time = local.localize(naive_order_time, is_dst=None)
                utc_dt_remit_time = (local_dt_remit_time.astimezone(UTC)).strftime("%Y-%m-%d %H:%M:%S")
                _logger.info("API : Remit Date Time %s UTC for PG REF %s", remit_date, params.get('pg_ref_no', False))
                vals.update({'remit_date': utc_dt_remit_time})
            except:
                _logger.info("API : Remit Date format for PG Ref No %s",
                             )
                raise APIError(status="REJECTED", status_code=402,
                               message="Invalid Remit Date Format")

        fields_to_update = ['remit_remarks', 'qwqer_ref_no', 'pg_ref_no', 'operation','remit_amount']
        for field in fields_to_update:
            if field in params:
                vals[field] = params.get(field, False) or False
        try:

            new_payin = request.env['driver.payin'].create(vals)
        except UniqueViolation as e:
            request.env.cr.rollback()
            err_msg = "Record already exist with pg_ref_no : " + vals['pg_ref_no']
            return {
                'remit_date': remit_date,
                'pg_ref_no': vals['pg_ref_no'],
                'status_code': 200,
                'status': "SUCCESS",
                'msg': err_msg
            }
        except Exception as e:
            raise APIError(status="REJECTED", status_code=500, message=e,
                           additional_params={'remit_date': remit_date, 'pg_ref_no': vals['pg_ref_no']})
        return {
            'remit_date': remit_date,
            'pg_ref_no': vals['pg_ref_no'],
            'status_code': 200,
            'status': "SUCCESS",
            'msg': "Driver Payin Created",
        }
