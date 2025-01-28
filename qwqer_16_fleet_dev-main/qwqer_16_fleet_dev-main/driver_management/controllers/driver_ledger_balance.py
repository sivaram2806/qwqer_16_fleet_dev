# -*- coding:utf-8 -*-

from datetime import datetime, timedelta
from odoo import http
from odoo import fields
import json
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError
import logging

_logger = logging.getLogger(__name__)


class DriverLedgerBalanceController(http.Controller):

    @http.route(['/driver_ledger_balance/request/'], type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def get_driver_ledger_balance(self, api_raw_log=None, **kwargs):
        """
        fetch driver ledger balance.
        """
        _logger.info("Driver Ledger Balance API: Request received at %s", fields.Datetime.now())
        try:
            if not kwargs:
                raise APIError(status="REJECTED", status_code=500, message="No Data Received or Incorrect Data Format")
            driver_id = kwargs.get('driver_id')
            if not driver_id:
                raise APIError(status="REJECTED", status_code=402, message="Mandatory fields missing: driver_id")
            driver = request.env['hr.employee'].sudo().search([('driver_uid', '=', driver_id)])
            if not driver:
                raise APIError(status="REJECTED", status_code=404,
                               message=f"Driver not found, invalid driver id: {driver_id}")
            up_to_date = datetime.combine(datetime.now().date() + timedelta(days=1), datetime.min.time())
            query = request.env['account.move.line']._where_calc([
                ('partner_id', '=', driver.related_partner_id.id),
                ('date', '<=', up_to_date.date()),
                ('account_id.is_driver_account', '=', True),
                ('parent_state', '=', 'posted'),
            ])
            from_clause, where_clause, where_clause_params = query.get_sql()
            sql = """
                    SELECT SUM(account_move_line.debit) as debit ,sum(account_move_line.credit) as credit  FROM %(from)s WHERE %(where)s 
                    """ % {'from': from_clause, 'where': where_clause}
            request.env.cr.execute(sql, where_clause_params)
            balance = request.env.cr.dictfetchall()
            closing_bal = 0.0
            if balance and balance[0]:
                balance = balance[0]
                debit = balance.get('debit') if balance.get('debit') else 0.0
                credit = balance.get('credit') if balance.get('credit') else 0.0
                closing_bal = round(debit - credit, 2)

            response = ({'status': "SUCCESS",
                         'status_code': 200,
                         'message': "Successfully fetched data",
                         'closing': closing_bal
                         })
            api_raw_log.update({
                'name': "Driver Ledger Balance API",
                'key': kwargs.get('driver_id'),
                "response": json.dumps(response),
                'response_date': fields.Datetime.now(),
                'status': response['status']})
            return json.dumps(response)
        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name="Driver Ledger Balance API")
        except Exception as e:
            _logger.error("Driver Ledger Balance API: Unexpected Error: %s", str(e))
            raise APIError(status="REJECTED", status_code=500,
                           message="An unexpected error occurred. Please try again later.")
