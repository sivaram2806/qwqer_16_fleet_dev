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


class DriverPlanUpdateCreationController(http.Controller):
    @http.route(['/driver/plan/sync'], type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def update_driver_plan(self, plan_name, driver_ids, action, payout_type, api_raw_log=None):
        """API to Create driver payin"""
        _logger.info(f"Received kwargs: Plan {plan_name}--{driver_ids}")
        if action == "remove":
            drivers = request.env['hr.employee'].search([('driver_uid', 'in', driver_ids)])
            drivers.update({"plan_detail_id": None, 'payout_type': payout_type})
            return json.dumps({})
        if plan_name:
            plan_id = request.env['driver.payout.plans'].search([('name', '=', plan_name)])
            if action == "add" and not plan_id:
                _logger.info(f"Received kwargs: Plan {plan_name}--{driver_ids}")
                api_raw_log.update({
                    "response": "plan missing",
                    'response_date': fields.Datetime.now(),
                    'name': "Plan Update from 13",
                    'status': "REJECTED"
                })
                return json.dumps({})
            if plan_id:
                drivers = request.env['hr.employee'].search([('driver_uid', 'in', driver_ids)])
                drivers.update({"plan_detail_id": plan_id.id,
                                'payout_type': payout_type})
                api_raw_log.update({
                    "response": "Plan Updated",
                    'response_date': fields.Datetime.now(),
                    'name': "Plan Update from 13",
                    'status': "SUCCESS"
                })
        return json.dumps({})
