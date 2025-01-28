# -*- coding:utf-8 -*-

import json
from datetime import datetime
import logging
import sys


_logger = logging.getLogger(__name__)

from odoo import http
from odoo import fields
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError


class WalletBulkDeduct(http.Controller):

    @http.route(['/wallet/bulk/deduct/'], type='json', methods=['POST'], auth='qwy_api_key', csrf=False)
    @check_auth_validity
    def wallet_bulk_deduct(self, api_raw_log=None, **kwargs):
        """
        Handles wallet bulk deduction functionality.
        """
        _logger.info("Wallet Bulk Deduct API: Request received at %s", fields.Datetime.now())

        try:
            # Validate input data
            if not kwargs:
                raise APIError(status="REJECTED", status_code=500, message="No Data Received or Incorrect Data Format!")

            # Mandatory fields validation
            mandatory_fields = ['wallet_id', 'transaction_ref_id', 'total_amount', 'order_date', 'order_list']
            missing_fields = [field for field in mandatory_fields if field not in kwargs]
            if missing_fields:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message=f"Mandatory fields missing: {', '.join(missing_fields)}"
                )

            # Normalize input parameters
            params = {k: (False if v is None else v) for k, v in kwargs.items()}

            # Validate wallet and customer
            wallet_id = params.get("wallet_id")
            customer_id = request.env['res.partner'].search([('wallet_id', '=', wallet_id)], limit=1)
            if not customer_id:
                raise APIError(status="REJECTED", status_code=500, message="Invalid wallet_id: Customer not found.")
            if not customer_id.is_wallet_active:
                raise APIError(status="REJECTED", status_code=500, message="Customer wallet is inactive.")

            # Validate total amount
            try:
                total_amount = float(params.get("total_amount"))
            except ValueError:
                raise APIError(status="REJECTED", status_code=500, message="Invalid total_amount format.")
            if total_amount <= 0:
                raise APIError(status="REJECTED", status_code=500, message="Total amount must be greater than zero.")

            # Validate order date
            try:
                order_date = datetime.strptime(params.get("order_date"), "%Y-%m-%d")
            except ValueError:
                raise APIError(status="REJECTED", status_code=500, message="Invalid order_date format. Use YYYY-MM-DD.")

            # Validate order_list
            order_list = params.get("order_list")
            if not isinstance(order_list, list) or not order_list:
                raise APIError(status="REJECTED", status_code=500, message="order_list must be a non-empty list.")

            # Validate orders and compute total from order_list
            order_total_sum, order_ids = self._validate_order_list(order_list)
            if round(total_amount, 2) != round(order_total_sum, 2):
                raise APIError(status="REJECTED", status_code=500, message="Total amount mismatch with order amounts.")

            # Check if sale orders already exist
            existing_orders = request.env['sale.order'].search([('order_id', 'in', order_ids)])
            if existing_orders:
                raise APIError(status="REJECTED", status_code=500, message="Order with same order id exists.")

            # Fetch wallet configuration
            wallet_config = request.env['customer.wallet.config'].search([('company_id','=',request.env.company.id)], limit=1)
            if not wallet_config or not wallet_config.journal_id or not wallet_config.wallet_inter_account_id:
                raise APIError(status="REJECTED", status_code=500, message="Invalid wallet configuration.")

            # Compute wallet balance
            wallet_balance = self._compute_wallet_balance(customer_id, wallet_config, fields.Date.today())
            if wallet_balance < total_amount:
                raise APIError(status="REJECTED", status_code=500, message="Insufficient wallet balance.")

            # Create and post journal entry
            je_vals = self._prepare_journal_entry_vals(params, customer_id, wallet_config, total_amount, order_list)
            move_id = self._create_or_post_account_move(params, je_vals)

            # Prepare response
            response = {
                'wallet_id': wallet_id,
                'erp_wallet_trans_ref_id': move_id.name,
                'transaction_ref_id': params.get('transaction_ref_id'),
                'balance': wallet_balance - total_amount,
                'status_code': 200,
                'status': "SUCCESS",
                'msg': "Successfully placed order with wallet amount.",
            }

            # Log API response
            if api_raw_log:
                api_raw_log.update({
                    'response': json.dumps(response),
                    'response_date': fields.Datetime.now(),
                    'key':  kwargs.get('wallet_id') and str(kwargs.get('wallet_id')),
                    'name': 'Wallet Bulk Deduct API',
                    'status': response['status']
                })

            return response

        except APIError as e:
            _logger.error("Wallet Bulk Deduct API: %s", e.message)
            return e.to_response(api_raw_log=api_raw_log, name="Wallet Bulk Deduct API")
        except Exception as e:
            _logger.exception("Unexpected error in Wallet Bulk Deduct API.")
            return APIError(
                status="error",
                status_code=500,
                message=f"Unexpected Error: {str(e)}"
            ).to_response(api_raw_log=api_raw_log, name="Wallet Bulk Deduct API")

    # Supporting Functions

    def _validate_order_list(self, order_list):
        """
        Validate the order_list and compute total amount and order IDs.
        """
        total_sum = 0
        order_ids = []

        for order in order_list:
            if 'order_id' not in order or 'order_amount' not in order:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message="Each order must contain 'order_id' and 'order_amount'."
                )
            try:
                total_sum += float(order['order_amount'])
            except ValueError:
                raise APIError(status="REJECTED", status_code=500, message="Invalid order_amount format.")
            order_ids.append(order['order_id'])

        return total_sum, order_ids

    def _compute_wallet_balance(self, customer, wallet_config, start_date=None):
        """
        Compute the wallet balance using raw SQL for performance.
        """
        domain = [
            ('partner_id', '=', customer.id),
            ('journal_id', '=', wallet_config.journal_id.id),
            ('account_id', '=', wallet_config.default_credit_account_id.id),
            ('parent_state', '=', 'posted'),
        ]
        if start_date:
            domain.append(('create_date', '<=', start_date))

        move_search = request.env['account.move.line']._where_calc(domain)
        tables, where_clause, where_params = move_search.get_sql()

        query = f"""
            SELECT 
                COALESCE(SUM(debit), 0) AS debit,
                COALESCE(SUM(credit), 0) AS credit,
                COALESCE(SUM(balance), 0) AS balance
            FROM {tables} 
            WHERE {where_clause}
        """
        request.env.cr.execute(query, where_params)
        result = request.env.cr.dictfetchone()

        return (result.get('balance', 0) or 0) * -1

    def _prepare_journal_entry_vals(self, params, customer, wallet_config, total_amount, order_list):
        """
        Prepare values for the account move journal entry.
        """
        lines = [
            {
                'partner_id': customer.id,
                'account_id': wallet_config.default_credit_account_id.id,
                'debit': total_amount,
                'credit': 0.0,
                'journal_id': wallet_config.journal_id.id,
                'name': "Deducted",
            }
        ]

        for order in order_list:
            lines.append({
                'partner_id': customer.id,
                'account_id': wallet_config.wallet_inter_account_id.id,
                'debit': 0.0,
                'journal_id': wallet_config.journal_id.id,
                'credit': float(order['order_amount']),
                'wallet_order_id': order['order_id'],
                'name': 'Deducted',
            })

        return {
            'move_type': 'entry',
            'ref': 'New Order',
            'service_type_id': request.env['partner.service.type'].search([('is_delivery_service','=',True)],limit=1).id,
            'partner_id': customer.id,
            'date': params.get('order_date'),
            'company_id': request.env.user.company_id.id,
            'currency_id': request.env.user.company_id.currency_id.id,
            'journal_id': wallet_config.journal_id.id,
            'line_ids': [(0, 0, line) for line in lines],
            'wallet_transaction_ref_id': params.get('transaction_ref_id'),
            'order_transaction_no': f"WD_{params.get('transaction_ref_id')}",
        }

    def _create_or_post_account_move(self, params, je_vals):
        """
        Create and post the account move.
        """
        account_move = request.env['account.move'].search([
            ('wallet_transaction_ref_id', '=', params.get('transaction_ref_id')),
            ('state', '=', 'posted'),
        ], limit=1)

        if not account_move:
            account_move = request.env['account.move'].create(je_vals)
            account_move.action_post()

        return account_move
