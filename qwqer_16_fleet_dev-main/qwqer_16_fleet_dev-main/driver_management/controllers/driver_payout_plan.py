import logging
from dataclasses import fields
from odoo import http
from odoo import fields
import json
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError

_logger = logging.getLogger(__name__)


class DriverPayoutPlan(http.Controller):
    @http.route('/driver/plan/fetch/', type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def driver_plan_fetch(self, api_raw_log=None, **kwargs):
        """API to get driver plan by driver uid """
        _logger.info("Received kwargs: %s", kwargs)
        driver_id = kwargs.get('driver_id', False)
        try:
            if driver_id:
                driver_data = request.env['hr.employee'].sudo().search([('driver_uid', '=', str(driver_id))])
                driver_list = []
                for driver in driver_data:
                    driver_list.append({
                        "plan_id": driver.plan_detail_id.id,
                        "plan_name": driver.plan_detail_id.name,
                        "driver_id": driver.driver_uid
                    })
                response = ({'status': "SUCCESS",
                             'status_code': 200,
                             'message': "Successfully fetched data",
                             'plan_details_list': driver_list
                             })
                api_raw_log.update({"response": json.dumps(response),
                                    'response_date': fields.Datetime.now(),
                                    'name': "Driver Plan Details Fetch",
                                    'key': driver_id and str(driver_id),
                                    'status': response['status']})
                return json.dumps(response)
            else:
                _logger.info("Service API : No Data Received or Incorrect Data Format!")
                raise APIError(status="REJECTED", status_code=500,
                               message="No Data Received or Incorrect Data Format!")

        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name="Driver Plan Details Fetch")
        except Exception as e:
            _logger.error(f"Service API : No Data Received or Incorrect Data Format!{str(e)}")
            error = APIError(status="error", status_code=500,
                             message="An unexpected error occurred. Please try again later")
            response = error.to_response(api_raw_log=api_raw_log, name="Driver Plan Details Fetch")
            return response

    @http.route(['/driver/payout/plan/details/', '/driver/payout/plan/list/'], type='json', methods=['POST'],
                auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def driver_payout_plan_details(self, api_raw_log=None, **kwargs):
        """API to get driver payout plan details by optional parameter as plan id, region """
        list_api = True if "list" in request.httprequest.base_url else False
        domain_list = []
        plan_details_list = []
        if 'plan_id' in kwargs:
            plan_id = kwargs.get('plan_id')
            domain_list.append(('id', '=', plan_id))
        if 'plan_name' in kwargs:
            plan_name = kwargs.get('plan_name')
            domain_list.append(('name', '=', plan_name))
        if 'region' in kwargs:
            region = kwargs.get('region')
            domain_list.append(('region_id.region_code', '=', region))
        if domain_list:
            plan_details = request.env['driver.payout.plans'].sudo().search(domain_list)
        else:
            plan_details = request.env['driver.payout.plans'].sudo().search([])
        minimum_wage_list = []
        distance_incentive_list = []
        distance_incentive_day_km_list = []
        distance_incentive_order_km_list = []
        daily_incentive_list = []
        daily_incentive_orders_list = []
        daily_incentive_hours_list = []
        daily_incentive_stop_counts_list = []
        weekend_incentive_list = []
        weekend_incentives = []
        weekend_holidays_list = []
        weekly_monthly_incentive_list = []
        weekly_incentive_list = []
        monthly_incentive_list = []
        try:
            if plan_details:
                for rec in plan_details:
                    dic = {
                        "plan_id": rec.id,
                        "plan_name": rec.name,
                        "region": rec.region_id.region_code,
                        "region_name": rec.region_id.name,
                        "default": rec.is_default_region_plan}
                    if not list_api:
                        if not kwargs:
                            status = "REJECTED"
                            status_code = 402
                            return json.loads(json.dumps({
                                'status': status,
                                'status_code': status_code,
                                'msg': "Mandatory Parameter Is Missing !!",
                            }))
                        for wage in rec.driver_minimum_wage_ids:
                            """Minimum Wage Values"""

                            wage = {
                                "min_no_of_hours": wage.min_hrs,
                                "min_orders": wage.min_orders,
                                "amount": wage.min_amount,
                            }
                            minimum_wage_list.append(wage)
                        """Distance Incentive Values"""

                        for dist in rec.day_incentive_order_km_ids:
                            incentive_day_km = {
                                "from_km": dist.start_km,
                                "to_km": dist.end_km,
                                "amount": dist.amount
                            }
                            distance_incentive_day_km_list.append(incentive_day_km)
                        for order in rec.incentive_order_km_ids:
                            incentive_order_km = {
                                "from_km": order.start_km,
                                "to_km": order.end_km,
                                "amount": order.amount
                            }
                            distance_incentive_order_km_list.append(incentive_order_km)
                        distance_incentive = {
                            "day_km": distance_incentive_day_km_list,
                            "order_km": distance_incentive_order_km_list
                        }
                        distance_incentive_list.append(distance_incentive)
                        """Daily incentive Orders"""

                        for daily in rec.daily_incentive_per_order_ids:
                            daily_incentive_orders = {
                                "from": daily.min_orders,
                                "to": daily.max_orders,
                                "amount": daily.amount_per_order
                            }
                            daily_incentive_orders_list.append(daily_incentive_orders)
                        for hours in rec.daily_incentive_per_hours_ids:
                            daily_incentive_hours = {
                                "from": hours.min_hours,
                                "to": hours.max_hours,
                                "amount": hours.amount_per_hour
                            }
                            daily_incentive_hours_list.append(daily_incentive_hours)
                        for stop_count in rec.daily_incentive_stop_count_ids:
                            daily_incentive_stop_counts = {
                                "from": stop_count.start_count,
                                "to": stop_count.end_count,
                                "amount": stop_count.amount_per_stop_count
                            }
                            daily_incentive_stop_counts_list.append(daily_incentive_stop_counts)

                        daily_incentive = {
                            "orders_list": daily_incentive_orders_list,
                            "hours_list": daily_incentive_hours_list,
                            "stop_counts_list": daily_incentive_stop_counts_list
                        }
                        daily_incentive_list.append(daily_incentive)

                        """Weekly / Monthly Incentive values"""

                        for wm in rec.weekly_incentive_ids:
                            weekly_incentive = {
                                "weekly_no_of_days": wm.no_of_days,
                                "weekly_min_of_hours": wm.min_hours,
                                "weekly_min_no_of_orders": wm.min_orders,
                                'weekly_incentive_amount': wm.amount,
                            }
                            weekly_incentive_list.append(weekly_incentive)
                        for mi in rec.monthly_incentive_ids:
                            monthly_incentive = {
                                "monthly_no_of_days": mi.no_of_days,
                                "monthly_min_of_hours": mi.min_hours,
                                "monthly_min_no_of_orders": mi.min_orders,
                                'monthly_incentive_amount': mi.amount,
                            }
                            monthly_incentive_list.append(monthly_incentive)
                        weekly_monthly = {
                            "weekly_incentive_list": weekly_incentive_list,
                            "monthly_incentive_list": monthly_incentive_list,
                        }
                        weekly_monthly_incentive_list.append(weekly_monthly)

                        """Weekend Incentive values """

                        for wi in rec.weekend_incentive_ids:
                            week_days_string = dict(wi._fields['week_days'].selection).get(wi.week_days)
                            weekend_incentive = {
                                "wi_day_of_week": week_days_string,
                                "wi_min_no_of_order": wi.min_orders,
                                "wi_min_no_of_hour": wi.min_hours,
                                'wi_amount': wi.amount,
                            }
                            weekend_incentives.append(weekend_incentive)
                        for wh in rec.holiday_incentive_ids:
                            weekend_holidays = {
                                "wi_holiday": wh.payout_plan_id.name,
                                "wi_holiday_date": str(wh.holiday_date),
                                "wi_holiday_min_no_of_orders": wh.min_no_of_order,
                                'wi_holiday_min_no_of_hours': wh.min_no_of_hr,
                                'wi_holiday_amount': wh.amount
                            }
                            weekend_holidays_list.append(weekend_holidays)
                        weekend = {
                            "weekend_incentives": weekend_incentives,
                            "weekend_holidays_list": weekend_holidays_list,
                        }
                        weekend_incentive_list.append(weekend)
                        dic.update({
                            "minimum_wage_list": minimum_wage_list,
                            "distance_incentive_list": distance_incentive_list,
                            "daily_incentive_list": daily_incentive_list,
                            "weekend_incentive_list": weekend_incentive_list,
                            "weekly_monthly_incentive_list": weekly_monthly_incentive_list
                        })
                    plan_details_list.append(dic)

                if plan_details_list:
                    response = ({
                        'plan_details_list': plan_details_list,
                        'status_code': 200,
                        'status': "SUCCESS",
                        'msg': "Plan Details Fetched Successfully",
                    })
                    api_raw_log.update({"response": json.dumps(response),
                                        'response_date': fields.Datetime.now(),
                                        'name': "Driver Payout Plan Details",
                                        'key': kwargs.get('plan_id') if kwargs.get('plan_id') else None,
                                        'status': response['status']})
                    return json.dumps(response)
            else:
                _logger.info("Service API : No Data Received or Incorrect Data Format!")
                raise APIError(status="REJECTED", status_code=500,
                               message="No Data Received or Incorrect Data Format!")

        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name="Driver Payout Plan Details")
        except Exception as e:
            _logger.error(f"Service API : No Data Received or Incorrect Data Format!{str(e)}")
            error = APIError(status="error", status_code=500,
                             message="An unexpected error occurred. Please try again later")
            response = error.to_response(api_raw_log=api_raw_log, name="Driver Payout Plan Details")
            return response
