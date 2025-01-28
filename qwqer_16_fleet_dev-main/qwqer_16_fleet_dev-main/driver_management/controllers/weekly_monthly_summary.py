import logging
from dataclasses import fields
import pytz
from odoo import http
from odoo import fields
import json
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError

_logger = logging.getLogger(__name__)


class WeeklyMonthlySummary(http.Controller):
    @http.route('/weekly_monthly_summary/request/', type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def weekly_monthly_summary_request(self, api_raw_log=None, **kwargs):
        """API to get driver plan by driver uid """
        _logger.info("Weekly Monthly Summary Request API: received at %s !!!", fields.Datetime.now())
        try:
            if not kwargs:
                raise APIError(status="REJECTED", status_code=500, message="No Data Received or Incorrect Data Format")
            required_fields = {
                'from_date': 'From Date',
                'to_date': 'To Date',
                'driver_id': 'Driver ID',
            }
            missing_field = next((field_name for field, field_name in required_fields.items() if not kwargs.get(field)),
                                 None)
            if missing_field:
                raise APIError(status="REJECTED", status_code=402, message=f"{missing_field} is missing")    
            batch_payout_lines = request.env['driver.batch.payout.lines'].search(
                [('driver_uid', '=', kwargs.get('driver_id')), ('to_date', '>=', kwargs.get('from_date')),
                 ('from_date', '<=', kwargs.get('to_date')), ('payment_state', '=', 'success')], order='from_date DESC')
            batch_payout_list = []
            if batch_payout_lines:
                for line in batch_payout_lines:
                    user_tz = request.env.user.tz or pytz.utc
                    local_tz = pytz.timezone(user_tz)
                    if line.processed_date:
                            utc_time = pytz.utc.localize(
                                line.processed_date) if not line.processed_date.tzinfo else line.processed_date
                            local_time = utc_time.astimezone(local_tz)
                            tz_processed_date = local_time.strftime("%d/%m/%Y %H:%M:%S")
                    else:
                        tz_processed_date = None
                    wm_payout_data = {
                            'from_date': str(line.from_date) if line.from_date else None,
                            'to_date': str(line.to_date) if line.to_date else None,
                            'name': line.transfer_id if line.transfer_id else None,
                            'driver_payout': round(line.daily_payout_amount, 2) if line.daily_payout_amount else None,
                            'incentive': round(line.incentive_amount, 2) if line.incentive_amount else None,
                            'deduction': round(line.deduction_amount, 2) if line.deduction_amount else None,
                            'tds_amount': round(line.tds_amount, 2) if line.tds_amount else None,
                            'processed_date': tz_processed_date if tz_processed_date else None,
                            'total_worked_hrs': line.daily_payout_ids and round(
                             sum(line.daily_payout_ids.mapped('worked_hours')), 2) or 0.0,
                            'total_orders': line.daily_payout_ids and sum(
                             line.daily_payout_ids.mapped('order_qty')) or 0,
                            'total_payout': round(line.total_payout, 2) if line.total_payout else 0.0
                     }
                    batch_payout_list.append(wm_payout_data)
                status = "SUCCESS"
                status_code = 200
                response = {
                    'status': status,
                    'status_code': status_code,
                    'msg': "successfully fetched data",
                    'payout_details': batch_payout_list
                }
                api_raw_log.update({"response": response,
                                    'response_date': fields.Datetime.now(),
                                    'name': "Weekly Monthly Payout Details",
                                    'key': kwargs.get('driver_id') and str(kwargs.get('driver_id')),
                                    'status': status})
                return json.dumps(response)
            raise APIError(status="REJECTED", status_code=402, message="No Data Found")
        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name="Weekly Monthly Payout Details")
        except Exception as e:
            _logger.error(f"Service API : No Data Received or Incorrect Data Format!{str(e)}")
            error = APIError(status="error", status_code=500,
                             message="An unexpected error occurred. Please try again later")
            response = error.to_response(api_raw_log=api_raw_log, name="Weekly Monthly Payout Details")
            return response
