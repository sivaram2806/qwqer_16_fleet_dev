import logging
from dataclasses import fields
from odoo import http
from odoo import fields
import json
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError

_logger = logging.getLogger(__name__)


class DailyPayoutDetails(http.Controller):
    @http.route('/daily_payout_details/request/', type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def daily_payout_details_request(self, api_raw_log=None, **kwargs):
        """API to get driver plan by driver uid """
        _logger.info("Daily Payout Details Request API: received at %s !!!", fields.Datetime.now())
        try:
            if not kwargs:
                raise APIError(status="REJECTED", status_code=500, message="No Data Received or Incorrect Data Format")
            transfer_id = kwargs.get('transfer_id')
            if transfer_id:
                payout_line_id = request.env['driver.batch.payout.lines'].search(
                    [('transfer_id', '=', kwargs.get('transfer_id'))], limit=1)
                payout_list = []
                if payout_line_id:
                    for daily_line in payout_line_id.daily_payout_ids:
                        payout_data = {
                            'date': str(daily_line.date) if daily_line.date else None,
                            'worked_hours': daily_line.worked_hours if daily_line.worked_hours else None,
                            'orders': daily_line.no_of_orders if daily_line.no_of_orders else None,
                            'total_distance': round(daily_line.total_distance, 2) if daily_line.total_distance else None,
                            'est_total_distance': round(daily_line.total_estimated_distance, 2) if daily_line.total_estimated_distance else None,
                            'minimum_wage': round(daily_line.minimum_wage, 2) if daily_line.minimum_wage else None,
                            'incentive_order': round(daily_line.order_km_incentive, 2) if daily_line.order_km_incentive else None,
                            'incentive_day': round(daily_line.day_km_incentive, 2) if daily_line.day_km_incentive else None,
                            'daily_incentive_orders': round(daily_line.orders_incentive, 2) if daily_line.orders_incentive else None,
                            'daily_incentive_hours': round(daily_line.hours_incentive, 2) if daily_line.hours_incentive else None,
                            'holiday_bonus': round(daily_line.holiday_incentive, 2) if daily_line.holiday_incentive else None,
                            'daily_payout': round(daily_line.total_payout, 2) if daily_line.total_payout else None,
                        }
                        payout_list.append(payout_data)
                    status = "SUCCESS"
                    status_code = 200
                    response = {
                        'status': status,
                        'status_code': status_code,
                        'msg': "successfully fetched data",
                        'payout_details': payout_list
                    }
                    self.update_api_raw_log(api_raw_log,response,transfer_id)
                    return json.dumps(response)
                else:
                    raise APIError(status="REJECTED", status_code=402, message="No data found. Please check the Transfer ID")
            else:
                from_date = kwargs.get('from_date')
                to_date = kwargs.get('to_date')
                driver_id = kwargs.get('driver_id')
                required_fields = {
                    'from_date': 'From Date',
                    'to_date': 'To Date',
                    'driver_id': 'Driver ID',
                }
                missing_field = next((field_name for field, field_name in required_fields.items() if not kwargs.get(field)), None)
                if missing_field:
                    raise APIError(status="REJECTED", status_code=402, message=f"{missing_field} Missing")
                driver_payouts = request.env['driver.payout'].search(
                    [('driver_uid', '=', driver_id), ('date', '>=', from_date),
                     ('date', '<=', to_date)], order='date DESC')
                driver_payout_list = []
                if driver_payouts:
                    for payout in driver_payouts:
                        driver_payout_data = {
                            'date': str(payout.date) if str(payout.date) else None,
                            'worked_hours': payout.worked_hours if payout.worked_hours else None,
                            'orders': payout.no_of_orders if payout.no_of_orders else None,
                            'total_distance': round(payout.total_distance, 2) if payout.total_distance else None,
                            'est_total_distance': round(payout.total_estimated_distance, 2) if payout.total_estimated_distance else None,
                            'minimum_wage': round(payout.minimum_wage, 2) if payout.minimum_wage else None,
                            'incentive_order': round(payout.order_km_incentive, 2) if payout.order_km_incentive else None,
                            'incentive_day': round(payout.day_km_incentive, 2) if payout.day_km_incentive else None,
                            'daily_incentive_orders': round(payout.orders_incentive, 2) if payout.orders_incentive else None,
                            'daily_incentive_hours': round(payout.hours_incentive, 2) if payout.hours_incentive else None,
                            'holiday_bonus': round(payout.holiday_incentive, 2) if payout.holiday_incentive else None,
                            'daily_payout': round(payout.total_payout, 2) if payout.total_payout else None,
                        }
                        driver_payout_list.append(driver_payout_data)
                    status = "SUCCESS"
                    status_code = 200
                    response = {
                        'status': status,
                        'status_code': status_code,
                        'msg': "successfully fetched data",
                        'payout_details': driver_payout_list
                    }
                    self.update_api_raw_log(api_raw_log,response,driver_id)
                    return json.dumps(response)
                else:
                    raise APIError(status="REJECTED", status_code=402, message="No data Found")
        except APIError as e:
            _logger.error("Daily Payout Details Request API: Unexpected Error: %s", str(e))
            return e.to_response(api_raw_log=api_raw_log, name="Daily Payout Details Request API")
        except Exception as e:
            _logger.error(f"Service API : No Data Received or Incorrect Data Format!{str(e)}")
            error = APIError(status="error", status_code=500,
                             message="An unexpected error occurred. Please try again later")
            response = error.to_response(api_raw_log=api_raw_log, name="Daily payout details Request")
            return response

    def update_api_raw_log(self,api_raw_log,response,key):
            api_raw_log.update({
                "response": response,
                'response_date': fields.Datetime.now(),
                'name': "Daily Driver Payout Details",
                'key': key and str(key),
                'status': response.get('status')
            })