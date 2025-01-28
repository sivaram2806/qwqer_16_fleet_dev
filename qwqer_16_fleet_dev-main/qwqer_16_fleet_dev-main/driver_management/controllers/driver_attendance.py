# -*- coding:utf-8 -*-

import pytz
import logging
from datetime import datetime
from odoo import http


logger = logging.getLogger(__name__)

from odoo import fields
import json
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError
import logging

_logger = logging.getLogger(__name__)

class DriverAttendanceController(http.Controller):

    @http.route(['/internal/attendance/request/'], type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def driver_attendance_create_update(self, api_raw_log=None, **kwargs):
        """
        Handles creating or updating driver attendance records.
        """
        _logger.info("Driver Attendance API: Request received, Processing ...... %s", fields.Datetime.now())

        try:
            # Validate input
            if not kwargs:
                msg = "No Data Received or Incorrect Data Format!"
                _logger.info("Driver Attendance API: %s", msg)
                raise APIError(status="REJECTED", status_code=500,
                               message=msg)

            # Check mandatory fields
            mandatory_fields = ['employee_id', 'attendance_id', 'date']
            missing_fields = [field for field in mandatory_fields if not kwargs.get(field)]
            if missing_fields:
                raise APIError(status="REJECTED", status_code=402,
                               message=f"Mandatory fields missing: {', '.join(missing_fields)}")

            params = {k: (False if v is None else v) for k, v in kwargs.items()}
            employee_id = params['employee_id']
            attendance_id = params['attendance_id']

            # Fetch employee record
            emp_id = request.env['hr.employee'].search([('driver_uid', '=', employee_id)])
            if not emp_id:
                raise APIError(status="REJECTED", status_code=500,
                               message=f"Invalid Employee ID: {employee_id}")

            # Fetch duplicate attendance record
            attendance_duplicate = request.env['hr.attendance'].search([('attendance_uid', '=', attendance_id)])
            if attendance_duplicate and attendance_duplicate.employee_id != emp_id:
                raise APIError(status="REJECTED", status_code=500,
                               message=f"Attendance record with same Attendance ID exists.")

            # Prepare attendance values
            vals = self._prepare_attendance_vals(params, emp_id)

            # Fetch or create attendance record
            attendance_rec = request.env['hr.attendance'].search([
                ('employee_id', '=', emp_id.id),
                ('attendance_uid', '=', attendance_id),
            ])

            if attendance_rec:
                attendance_rec.write(vals)
                log_name = "Driver Attendance Update"
                _logger.info("Driver Attendance API: Attendance updated for ID: %s", attendance_id)
            else:
                attendance_rec = request.env['hr.attendance'].create(vals)
                log_name = "Driver Attendance Create"
                _logger.info("Driver Attendance API: Attendance created for ID: %s", attendance_rec)

            response = {
                'status': "SUCCESS",
                'status_code': 200,
                'msg': "Attendance processed successfully",
            }

            # Update API raw log
            self._update_api_log(api_raw_log, response, log_name, employee_id)
            return json.dumps(response)

        except APIError as e:
            _logger.error("Driver Attendance API: Unexpected Error: %s", str(e))
            return e.to_response(api_raw_log=api_raw_log, name="Driver Attendance API")
        except Exception as e:
            msg = "Driver Attendance API: Unexpected Error: %s" % str(e)
            _logger.error(msg)
            error = APIError(status="error", status_code=500,
                             message=msg)
            response = error.to_response(api_raw_log=api_raw_log, name="Driver Attendance API")
            return response

    def _parse_datetime_field(self, date_str, error_msg, api_raw_log):
        """
        Parse datetime fields and convert to UTC.
        """
        try:
            local_tz = pytz.timezone(request.env.user.tz or 'UTC')
            naive_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            local_dt = local_tz.localize(naive_date, is_dst=None)
            return local_dt.astimezone(pytz.utc).replace(tzinfo=None)
        except Exception as e:
            msg = "Driver Attendance API: Unexpected Error: %s" % str(e)
            _logger.error(msg)
            error = APIError(status="error", status_code=500, message=msg)
            response = error.to_response(api_raw_log=api_raw_log, name="Driver Attendance API")
            return response

    def _prepare_attendance_vals(self, params, emp_id):
        """
        Prepare values for attendance record.
        """
        vals = {
            'employee_id': emp_id.id,
            'employee_code': params['employee_id'],
            'attendance_uid': params['attendance_id'],
            'company_id': emp_id.company_id.id,
            'date': params['date'],
            'region_id': emp_id.region_id.id,
            'app_total_distance': params.get('app_total_distance', False),
            'app_working_hours': params.get('app_working_hours', False),
            'check_in': False,
            'check_out': False
        }

        # Validate and process datetime fields
        datetime_fields = {
            'check_in': 'Invalid check-in Date Format',
            'check_out': 'Invalid check-out Date Format',
        }
        for field, error_msg in datetime_fields.items():
            if field in params:
                parsed_date = self._parse_datetime_field(params[field], error_msg, None)
                if parsed_date:
                    vals[field] = parsed_date
        return vals

    def _update_api_log(self, api_raw_log, response, log_name, employee_id):
        """
        Update the API raw log with response details.
        """
        api_raw_log.update({
            "response": json.dumps(response),
            "response_date": fields.Datetime.now(),
            "name": log_name,
            "key": str(employee_id),
            "status": response['status'],
        })
        _logger.info("Driver Attendance API: log updated: %s", log_name)
