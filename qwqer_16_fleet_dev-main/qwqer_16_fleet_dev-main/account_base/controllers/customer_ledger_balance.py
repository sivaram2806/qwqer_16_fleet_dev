# -*- coding:utf-8 -*-

from odoo import http
import json

from odoo import fields
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError
import logging

_logger = logging.getLogger(__name__)

class CustomerLedgerBalanceController(http.Controller):

    @http.route(['/customer_ledger_balance/request/'], type='json', methods=['POST'], auth='qwy_api_key', csrf=False)
    @check_auth_validity
    def customer_ledger_balance_fetch(self, api_raw_log=None, **kwargs):
        """
        Handles customer ledger balance fetching records.
        """
        _logger.info("Customer Ledger Balance API: Request received, Processing ...... %s", fields.Datetime.now())

        try:
            # Validate input
            if not kwargs:
                msg = "No Data Received or Incorrect Data Format!"
                _logger.info("Customer Ledger Balance API: %s", msg)
                raise APIError(status="REJECTED", status_code=500,
                               message=msg)

            # Check mandatory fields
            mandatory_fields = ['customer_id']
            missing_fields = [field for field in mandatory_fields if not kwargs.get(field)]
            if missing_fields:
                raise APIError(status="REJECTED", status_code=500,
                               message=f"Customer Ledger Balance API: Mandatory fields missing: {', '.join(missing_fields)}")

            params = {k: (False if v is None else v) for k, v in kwargs.items()}

            # Fetch customer record
            customer_id = request.env['res.partner'].search([('id', '=', params.get('customer_id'))])
            if not customer_id or customer_id.supplier_rank > 0:
                raise APIError(status="REJECTED", status_code=500,
                               message=f"Customer Ledger Balance API: Invalid Customer ID: {customer_id.name}")
            if customer_id.customer_type != 'b2b':
                raise APIError(status="REJECTED", status_code=500,
                               message=f"Customer Ledger Balance API: Customer ID should be B2B type: {customer_id.name}")

            sql = """
            SELECT
                RP.id AS partner_id,
                COALESCE(SUM(SO.amount_total), 0.00) AS amount_total,
                COALESCE(SUM(AML.balance), 0.00) AS rp_balance,
                COALESCE(SUM(DAML.daml_balance), 0.00) AS daml_balance,
                COALESCE(SUM(WAL.wal_balance), 0.00) AS wal_balance,
                COALESCE(AML.balance, 0.00) + COALESCE(SO.amount_total, 0.00) +
                COALESCE(SUM(DAML.daml_balance), 0.00) - COALESCE(SUM(WAL.wal_balance), 0.00) AS balance
            FROM
                res_partner RP
            LEFT JOIN (
                SELECT
                    aml.partner_id AS partner_id,
                    COALESCE(SUM(aml.balance), 0.00) AS balance
                FROM
                    account_move_line aml
                WHERE
                    aml.account_id IN (
                        SELECT id
                        FROM account_account aa
                        WHERE account_type IN ('liability_payable', 'asset_receivable')
                    )
                    AND aml.parent_state = 'posted'
                GROUP BY
                    aml.partner_id
            ) AS AML ON RP.id = AML.partner_id
            LEFT JOIN (
                SELECT
                    so.partner_id AS partner_id,
                    COALESCE(SUM(so.amount_total), 0.00) AS amount_total
                FROM
                    sale_order so
                WHERE
                    so.invoice_status = 'to invoice'
                GROUP BY
                    so.partner_id
            ) AS SO ON RP.id = SO.partner_id
            LEFT JOIN (
                SELECT
                    aml.partner_id AS partner_id,
                    aml.name,
                    COALESCE(SUM(aml.balance), 0.00) AS daml_balance
                FROM
                    account_move_line aml
                LEFT JOIN account_move am ON aml.move_id = am.id
                LEFT JOIN payment_mode pm ON am.payment_mode_id = pm.id
                WHERE
                    aml.account_id IN (
                        SELECT id
                        FROM account_account aa
                        WHERE account_type IN ('liability_payable', 'asset_receivable')
                    )
                    AND aml.parent_state = 'draft'
                    AND aml.partner_id IS NOT NULL
                    AND am.consolidated_invoice_id IS NOT NULL
                    AND pm.is_credit_payment = TRUE
                GROUP BY
                    aml.partner_id,
                    aml.name
            ) AS DAML ON RP.id = DAML.partner_id
            LEFT JOIN (
                SELECT
                    aml.partner_id AS partner_id,
                    COALESCE(SUM(aml.balance), 0.00) * -1 AS wal_balance
                FROM
                    account_move_line aml
                WHERE
                    aml.parent_state = 'posted'
                    AND aml.partner_id IS NOT NULL
                    AND aml.account_id = (
                        SELECT default_debit_account_id
                        FROM customer_wallet_config
                        LIMIT 1
                    )
                    AND aml.journal_id = (
                        SELECT journal_id
                        FROM customer_wallet_config
                        LIMIT 1
                    )
                GROUP BY
                    aml.partner_id
            ) AS WAL ON RP.id = WAL.partner_id
            WHERE
                RP.customer_rank > 0
                AND RP.active = TRUE
                AND RP.customer_type = 'b2b'
                AND RP.service_type_id IN (
                    SELECT id
                    FROM partner_service_type
                    WHERE is_delivery_service = TRUE
                )
                AND RP.id = %s
            GROUP BY
                RP.id, aml.balance, so.amount_total""" % customer_id.id
            request.env.cr.execute(sql)
            partner_balance = request.env.cr.dictfetchall()
            closing_bal = 0.00
            if partner_balance:
                closing_bal = partner_balance and partner_balance[0] and partner_balance[0]['balance'] or 0.00
            response = {
                'status': "SUCCESS",
                'status_code': 200,
                'msg': "successfully Fetched Data",
                'closing': round(closing_bal, 2),
            }

            # Update API raw log
            api_raw_log.update({
                "response": json.dumps(response),
                "response_date": fields.Datetime.now(),
                "name": 'Customer Ledger Balance API',
                "key": str(customer_id),
                "status": response['status'],
            })
            _logger.info("Customer Ledger Balance API: log updated: Customer Ledger Balance Fetched and sent Successfully !!!")
            return json.dumps(response)


        except APIError as e:
            _logger.error("Customer Ledger Balance API: Unexpected Error: %s", str(e))
            return e.to_response(api_raw_log=api_raw_log, name="Customer Ledger Balance API")
        except Exception as e:
            msg = "Customer Ledger Balance API: Unexpected Error: %s" % str(e)
            _logger.error(msg)
            error = APIError(status="error", status_code=500,
                             message=msg)
            response = error.to_response(api_raw_log=api_raw_log, name="Customer Ledger Balance API")
            return response