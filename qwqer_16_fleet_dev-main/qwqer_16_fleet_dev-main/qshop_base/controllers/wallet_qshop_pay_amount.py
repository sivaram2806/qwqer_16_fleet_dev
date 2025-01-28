# -*- coding:utf-8 -*-

from datetime import datetime, timedelta
from odoo import http
from odoo import fields
import json
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError
import logging
import sys

_logger = logging.getLogger(__name__)


class QshopWalletPayAmountController(http.Controller):

    @http.route(['/wallet/qshop/pay/amount/'], type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def wallet_qshop_pay_amount(self, api_raw_log=None, **kwargs):
        """
        Make Qshop customer wallet orders payment.
        """

        def get_wallet_balance():
            """helper to fetch customer wallet balance"""
            try:
                wallet_bal = request.env['res.partner'].sudo().compute_wallet_balance(
                    partner, wallet_config, fields.Date.today(self)
                )
            except Exception as e:
                raise APIError(status="REJECTED", status_code=500, message=str(e),
                               additional_params={'wallet_id': wallet_id, 'order_id': order_id})
            return wallet_bal

        def qshop_wallet_merchant_amount_deduct():
            """helper to create merchant amount deduction move"""
            if merchant_amount > 0:
                try:
                    merchant_order_transaction_no = "QMWD_" + transaction_ref_id
                    merchant_account_move = request.env['account.move'].sudo().search(
                        [('wallet_order_id', '=', order_id),
                         ('wallet_transaction_ref_id', '=', transaction_ref_id),
                         ('is_wallet_merchant_journal', '=', True), ('state', '=', 'posted'),
                         ('order_transaction_no', '=', merchant_order_transaction_no)])
                    if not merchant_account_move:
                        merchant_move_lines = [{
                            'partner_id': partner.id,
                            'account_id': wallet_config.default_credit_account_id.id or False,
                            'credit': 0.0,
                            'debit': merchant_amount,
                            'journal_id': wallet_config.journal_id.id or False,
                            'name': 'Merchant Deducted',
                            'wallet_order_id': order_id,
                            'service_type_id': qshop_service_type.id
                        },
                            {
                                'partner_id': partner.id,
                                'account_id': wallet_config.merchant_inter_account_id.id,
                                'credit': merchant_amount,
                                'debit': 0.0,
                                'journal_id': wallet_config.journal_id.id,
                                'name': "Merchant Deducted",
                                'wallet_order_id': order_id,
                                'service_type_id': qshop_service_type.id

                            }]
                        merchant_account_move_vals = {
                            'partner_id': partner.id,
                            'journal_id': wallet_config.journal_id.id,
                            'line_ids': [(0, 0, line) for line in merchant_move_lines],
                            'move_type': "entry",
                            'wallet_order_id': order_id,
                            'wallet_transaction_ref_id': transaction_ref_id,
                            'order_transaction_no': merchant_order_transaction_no,
                            'date': order_date,
                            'ref': "Merchant Order - " + order_id,
                            'company_id': request.env.company.id,
                            'service_type_id': qshop_service_type.id,
                            'is_wallet_merchant_journal': True,
                        }

                        merchant_account_move = request.env['account.move'].sudo().create(merchant_account_move_vals)
                        merchant_account_move.sudo().post()
                except Exception as e:
                    raise APIError(status="REJECTED", status_code=500, message=str(e),
                                   additional_params={'wallet_id': wallet_id, 'order_id': order_id})

        def qshop_wallet_amount_deduct():
            """helper to create  amount deduction move"""
            try:
                move_lines = [
                    {
                        'partner_id': partner.id,
                        'account_id': wallet_config.default_credit_account_id.id,
                        'debit': amount,
                        'credit': 0.0,
                        'journal_id': wallet_config.journal_id.id,
                        'name': "Deducted",
                        'wallet_order_id': order_id,
                        'service_type_id': qshop_service_type.id
                    },
                    {
                        'partner_id': partner.id,
                        'account_id': wallet_config.wallet_inter_account_id.id,
                        'debit': 0.0,
                        'credit': amount,
                        'journal_id': wallet_config.journal_id.id,
                        'name': "Deducted",
                        'wallet_order_id': order_id,
                        'service_type_id': qshop_service_type.id
                    },
                ]
                account_move_vals = {
                    'partner_id': partner.id,
                    'journal_id': wallet_config.journal_id.id,
                    'line_ids': [(0, 0, line) for line in move_lines],
                    'move_type': "entry",
                    'wallet_order_id': order_id,
                    'wallet_transaction_ref_id': transaction_ref_id,
                    'order_transaction_no': order_transaction_no,
                    'date': order_date,
                    'ref': "New Order - " + order_id,
                    'company_id': request.env.company.id,
                    'service_type_id': qshop_service_type.id
                }

                account_move = request.env['account.move'].sudo().create(account_move_vals)
                account_move.sudo().post()

                # Recalculate wallet balance
                wallet_bal = get_wallet_balance()

                return {
                    'status': "SUCCESS",
                    'status_code': 200,
                    'message': "Successfully placed order with wallet amount.",
                    'wallet_id': wallet_id,
                    'erp_wallet_trans_ref_id': account_move.name,
                    'transaction_ref_id': transaction_ref_id,
                    'order_id': order_id,
                    'balance': wallet_bal,
                }
            except Exception as e:
                raise APIError(status="REJECTED", status_code=500, message=str(e),
                               additional_params={'wallet_id': wallet_id, 'order_id': order_id})

        api_name = 'Qshop Wallet Pay Amount Service API'
        _logger.info("%s: Request received at %s", api_name, fields.Datetime.now())

        try:
            # Validate request data
            if not kwargs:
                raise APIError(status="REJECTED", status_code=500, message="No Data Received or Incorrect Data Format")

            mandatory_fields = ['wallet_id', 'order_id', 'transaction_ref_id', 'order_date']
            missing_fields = [field for field in mandatory_fields if not kwargs.get(field)]
            if missing_fields:
                raise APIError(
                    status="REJECTED",
                    status_code=402,
                    message=f"Mandatory fields missing: {', '.join(missing_fields)}"
                )
            if kwargs.get('amount') in [None,""]:

                raise APIError(
                    status="REJECTED",
                    status_code=402,
                    message="Amount is missing",
                    additional_params={'wallet_id': kwargs.get('wallet_id'), 'order_id':  kwargs.get('order_id')}
                )
            if kwargs.get('amount') < 0:
                raise APIError(
                    status="REJECTED",
                    status_code=402,
                    message="Amount must be greater than 0.",
                    additional_params={'wallet_id': kwargs.get('wallet_id'), 'order_id': kwargs.get('order_id')}
                )


            wallet_id = kwargs.get('wallet_id')
            order_id = kwargs.get('order_id')
            transaction_ref_id = kwargs.get('transaction_ref_id')
            amount = float(kwargs.get('amount', 0))
            merchant_amount = float(kwargs.get('merchant_amount', 0))
            order_date = kwargs.get('order_date')
            order_transaction_no = f"WD_{transaction_ref_id}"



            # Validate order date format
            try:
                order_dt = datetime.strptime(order_date, "%Y-%m-%d")
            except ValueError:
                raise APIError(
                    status="REJECTED",
                    status_code=402,
                    message="Invalid Transaction Date format.",
                    additional_params={'wallet_id': wallet_id, 'order_id': order_id}
                )

            # Check if the order already exists
            if request.env['sale.order'].sudo().search([('order_id', '=', order_id)]):
                raise APIError(
                    status="REJECTED",
                    status_code=402,
                    message=f"Sale order already exists with the order ID {order_id}.",
                    additional_params={'wallet_id': wallet_id, 'order_id': order_id}
                )

            # Fetch partner and validate wallet
            partner = request.env['res.partner'].sudo().search([('wallet_id', '=', wallet_id)], limit=1)
            if not partner:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message=f"Missing partner for wallet ID {wallet_id}.",
                    additional_params={'wallet_id': wallet_id, 'order_id': order_id}
                )
            if not partner.is_wallet_active:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message="Customer wallet is not active.",
                    additional_params={'wallet_id': wallet_id, 'order_id': order_id}
                )

            # Determine payment mode and adjust amount
            merchant_payment_mode = kwargs.get('merchant_payment_mode', 6)
            pay_amount = amount + merchant_amount

            mode_val = request.env['payment.mode'].sudo().search([('code', '=', merchant_payment_mode)], limit=1)
            if not mode_val or not mode_val.is_wallet_payment:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message="Invalid or unsupported payment mode.",
                    additional_params={'wallet_id': wallet_id, 'order_id': order_id}
                )

            # Validate wallet configuration
            wallet_config = request.env['customer.wallet.config'].sudo().search(
                [('company_id', '=', request.env.company.id)],
                limit=1
            )
            if not wallet_config or not wallet_config.journal_id or not wallet_config.wallet_inter_account_id:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message="Incomplete wallet configuration.",
                    additional_params={'wallet_id': wallet_id, 'order_id': order_id}
                )

            # Check wallet balance
            wallet_bal = get_wallet_balance()
            wallet_entry = request.env['account.move'].sudo().search(
                [('wallet_order_id', '=', order_id), ('wallet_transaction_ref_id', '=', transaction_ref_id),
                 ('state', '=', 'posted'), ('order_transaction_no', '=', order_transaction_no),
                 ('is_wallet_merchant_journal', '=', False), ("company_id", "=", request.env.company.id)], limit=1)
            if wallet_entry:
                response = ({'status': "SUCCESS",
                             'status_code': 200,
                             'message': "Successfully placed order with wallet amount",
                             'wallet_id': wallet_id,
                             'erp_wallet_trans_ref_id': wallet_entry.sudo().name or False,
                             'transaction_ref_id': transaction_ref_id,
                             'order_id': order_id,
                             'balance': wallet_bal})
                api_raw_log.update({
                    'name': api_name,
                    'key': kwargs.get('wallet_id'),
                    "response": json.dumps(response),
                    'response_date': fields.Datetime.now(),
                    'status': response.get('status')})
                return json.dumps(response)

            if wallet_bal < pay_amount:
                raise APIError(status="REJECTED", status_code=500, message="Insufficient wallet balance.",
                               additional_params={'wallet_id': wallet_id, 'order_id': order_id})
            qshop_service_type = request.env['partner.service.type'].search(
                [('is_qshop_service', '=', True), ("company_id", "=", request.env.company.id)], limit=1)
            qshop_wallet_merchant_amount_deduct()
            response = qshop_wallet_amount_deduct()
            api_raw_log.update({
                'name': api_name,
                'key': kwargs.get('wallet_id'),
                "response": json.dumps(response),
                'response_date': fields.Datetime.now(),
                'status': response.get('status')})
            return json.dumps(response)
        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name=api_name)
        except Exception as e:
            _logger.error("%s: Unexpected Error: %s", api_name, str(e))
            raise APIError(status="REJECTED", status_code=500,
                           message="An unexpected error occurred. Please try again later.")
