# -*- coding:utf-8 -*-

import logging
from datetime import datetime
from odoo import http
import itertools
import json

from odoo.http import request

logger = logging.getLogger(__name__)

from odoo import fields
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError
import logging

_logger = logging.getLogger(__name__)

class DriverLedgerController(http.Controller):
    @http.route(['/driver_ledger/request/'], type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def driver_ledger_request(self, api_raw_log=None, **kwargs):
        """
        Handles driver ledger requests to fetch and compute ledger details.
        """
        _logger.info("Driver Ledger Request API: Request received at %s !!!", fields.Datetime.now())

        try:
            # Validate input
            if not kwargs:
                msg = f"No Data Received or Incorrect Data Format!"
                _logger.info("Driver Ledger Request API: %s", msg)
                raise APIError(status="REJECTED", status_code=500, message=msg)

            # Check mandatory fields
            mandatory_fields = ['driver_id', 'from_date', 'to_date']
            missing_fields = [field for field in mandatory_fields if not kwargs.get(field)]
            if missing_fields:
                msg = f"Mandatory fields missing: {', '.join(missing_fields)}"
                _logger.info("Driver Ledger Request API: %s", msg)
                raise APIError(status="REJECTED", status_code=402, message=msg)

            # Extract parameters
            driver_uid = kwargs.get('driver_id')
            from_date = kwargs.get('from_date')
            to_date = kwargs.get('to_date')

            # Compute opening balance
            opening_balance = self._compute_opening_balance(driver_uid, from_date)

            # Fetch ledger lines
            line_ids = self._fetch_ledger_lines(driver_uid, from_date, to_date)

            # Process ledger lines
            ledger_details, closing_balance = self._process_ledger_lines(line_ids, opening_balance)

            # Prepare response
            response = {
                'status': "SUCCESS",
                'status_code': 200,
                'msg': "Driver Ledger data fetched successfully",
                'opening': opening_balance,
                'closing': round(closing_balance, 2),
                'ledger_details': ledger_details,
            }

            # Update API raw log
            api_raw_log.update({
                "response": json.dumps(response),
                "response_date": fields.Datetime.now(),
                "name": 'Driver Ledger Request API',
                "key": str(driver_uid),
                "status": response['status'],
            })
            _logger.info("Driver Ledger Request API: log updated: Driver Ledger Fetched and sent Successfully !!!")
            return json.dumps(response)

        except APIError as e:
            _logger.error("Driver Ledger Request API: Unexpected Error: %s", str(e))
            return e.to_response(api_raw_log=api_raw_log, name="Driver Ledger API")
        except Exception as e:
            _logger.error("Driver Ledger Request API: Unexpected Error: %s", str(e))
            error = APIError(status="error", status_code=500,
                             message="Driver Ledger Request API: Unexpected Error: %s" % str(e))
            response = error.to_response(api_raw_log=api_raw_log, name="Driver Ledger API")
            return response

    def _compute_opening_balance(self, driver_uid, from_date):
        """
        Compute the opening balance for the given driver before the specified date.
        """

        sql = """
        select
            SUM(account_move_line.debit) as debit,
            SUM(account_move_line.credit) as credit,
            account_move_line.driver_uid
        from
            "account_move_line"
        left join "account_account" as "account_move_line__account_id" on
            ("account_move_line"."account_id" = "account_move_line__account_id"."id")
        where 
            CAST(account_move_line.driver_uid AS INTEGER) = %s 
            and "account_move_line__account_id"."is_driver_account" = TRUE
            and "account_move_line"."parent_state" = 'posted'
            and "account_move_line"."partner_id" is not null
            and "account_move_line"."date" < '%s'
        group by account_move_line.driver_uid 
        """ % (driver_uid, from_date)

        request.env.cr.execute(sql)
        result = request.env.cr.dictfetchall()

        if result and result[0]:
            debit = result[0].get('debit', 0.0) or 0.0
            credit = result[0].get('credit', 0.0) or 0.0
            return round(debit - credit, 2)
        return 0.0

    def _fetch_ledger_lines(self, driver_uid, from_date, to_date):
        """
        Fetch ledger lines for the given driver within the specified date range.
        """
        query = request.env['account.move.line']._where_calc(self.prepare_query(driver_uid, from_date, to_date))
        from_clause, where_clause, where_clause_params = query.get_sql()

        sql = """
            SELECT account_move_line.id as move_line_ids
            FROM %(from)s WHERE %(where)s
            ORDER BY account_move_line.create_date ASC
        """ % {'from': from_clause, 'where': where_clause}

        request.env.cr.execute(sql, where_clause_params)
        line_id_list = list(itertools.chain(*request.env.cr.fetchall()))
        return request.env['account.move.line'].sudo().browse(line_id_list)

    def _process_ledger_lines(self, line_ids, opening_balance):
        """
        Process ledger lines and compute closing balance.
        """
        last_date_threshold = datetime.strptime('2022-02-01', '%Y-%m-%d').date()
        closing_balance = opening_balance

        ledger_details = []
        for line in line_ids:
            ledger_details.insert(0, {
                'date': str(line.date),
                'entry_id': self._determine_entry_details(line, last_date_threshold)[1],
                'entry_type': self._determine_entry_details(line, last_date_threshold)[0],
                'credit': line.credit,
                'debit': line.debit,
                'balance': round(closing_balance := closing_balance + round(line.debit - line.credit, 2), 2),
            })

        return ledger_details, closing_balance

    def _determine_entry_details(self, line, last_date_threshold):
        """
        Determine entry type and ID based on the line's attributes.
        """
        if line.date < last_date_threshold:
            if line.merchant_order_id:
                return 'Merchant Amount', line.merchant_order_id.order_id
            journal_name = line.journal_id.name.lower()
            if "airtel" in journal_name:
                return 'Payin via Airtel', ''
            elif "payin" in journal_name:
                return 'Driver Payin', ''
            elif "collection" in journal_name:
                return 'Delivery Charges', ''
        if line.name == 'Payout Deduction':
            return 'Payout', line.ref
        return line.name, line.ref

    def prepare_query(self, driver_uid, from_date, to_date=None):
        """
        Prepare domain filters for account.move.line query.
        """
        domain = [
            ('driver_uid', '=', driver_uid),
            ('account_id.is_driver_account', '=', True),
            ('parent_state', '=', 'posted'),
            ('partner_id', '!=', False),
        ]
        if to_date:
            domain += [('date', '>=', from_date), ('date', '<=', to_date)]
        else:
            domain.append(('date', '<', from_date))
        return domain
