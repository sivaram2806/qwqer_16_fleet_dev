# coding=utf-8
import logging
import sys

import pytz
import json
from datetime import datetime
from odoo import http, fields
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError

_logger = logging.getLogger(__name__)


class WalletDeductAmountAPI(http.Controller):

    @http.route('/wallet/pay/amount/', type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def deduct_amount(self, api_raw_log=None, **kwargs):
        """API to deduct amount from customer wallet"""
        try:
            params = {k: (False if v is None else v) for k, v in kwargs.items()}
            if not kwargs:
                raise APIError(status="REJECTED", status_code=500,
                               message="No Data Received or Incorrect Data Format!")
            _logger.info("Wallet Deduct API : Request Received, Processing ...")
            wallet_id, order_id, transaction_ref_id, amount, order_date = self._validate_request(params)
            local_tz = pytz.timezone(request.env.user.tz or 'UTC')
            self._parse_order_date(order_date, local_tz)

            _logger.info(f"Processing wallet deduction for wallet_id: {wallet_id}, order_id: {order_id}")

            response = self._process_wallet_deduction(wallet_id, order_id, transaction_ref_id, amount, params)

            api_raw_log.update({
                "response": json.dumps(response),
                'response_date': fields.Datetime.now(),
                'name': "Partner Wallet Deduction",
                'key': wallet_id,
                'status': response['status']
            })
            return json.dumps(response)

        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name="Wallet Deduct API")
        except Exception as e:
            _logger.error(f"Unexpected error: {str(e)}")
            error = APIError(status="error", status_code=500,
                             message="An unexpected error occurred. Please try again later.")
            return error.to_response(api_raw_log=api_raw_log, name="Wallet Deduct API")

    def _validate_request(self, data):
        """Validate mandatory request parameters."""

        _logger.info(f"Processing wallet deduction Required Fields")

        wallet_id = data.get('wallet_id')
        order_id = data.get('order_id')
        transaction_ref_id = data.get('transaction_ref_id')
        order_date = data.get('order_date')

        try:
            amount = float(data.get('amount', 0))
        except ValueError:
            raise APIError(status="REJECTED", status_code=402, message="Mandatory Parameter Amount is Missing")

        if not wallet_id:
            raise APIError(status="REJECTED", status_code=402, message="Mandatory Parameter Wallet ID Missing")
        if not order_id:
            raise APIError(status="REJECTED", status_code=402, message="Mandatory Parameter Order ID Missing")
        if not transaction_ref_id:
            raise APIError(status="REJECTED", status_code=402,
                           message="Mandatory Parameter Transaction Reference ID Missing")
        if amount <= 0:
            raise APIError(status="REJECTED", status_code=402, message="Amount must be greater than 0")
        if not order_date:
            raise APIError(status="REJECTED", status_code=402, message="Mandatory Parameter Order Date Missing")

        return wallet_id, order_id, transaction_ref_id, amount, order_date

    def _parse_order_date(self, order_date, local_tz):
        """Parse and validate order date."""
        try:
            order_dt = datetime.strptime(order_date, "%Y-%m-%d")
            return local_tz.localize(order_dt)
        except Exception:
            raise APIError(status="REJECTED", status_code=402, message="Invalid Order Date Format")

    def _process_wallet_deduction(self, wallet_id, order_id, transaction_ref_id, amount, data):
        """Perform wallet deduction process."""
        partner = request.env['res.partner'].search([('wallet_id', '=', wallet_id)], limit=1)
        vals = {}
        if not partner:
            raise APIError(status="REJECTED", status_code=402, message="Partner not found for Wallet ID")
        if not partner.is_wallet_active:
            raise APIError(status="REJECTED", status_code=402, message="Customer wallet is not active")
        order_date = data.get('order_date')
        if order_date:
            vals.update({'date': order_date or False})
        if order_id:
            vals.update({'wallet_order_id': order_id or False})
            vals.update({'ref': "New Order - " + order_id or False})
            sale_order_exists = request.env['sale.order'].search_count([('order_id', '=', order_id)])
            if sale_order_exists:
                return {
                    'wallet_id': wallet_id,
                    'order_id': order_id,
                    'status_code': 200,
                    'status': "SUCCESS",
                    'msg': "Sale order already exist with the order id"
                }
        if transaction_ref_id:
            vals.update({'wallet_transaction_ref_id': transaction_ref_id})
            vals.update({'order_transaction_no': "WD_" + transaction_ref_id})

        wallet_config = request.env['customer.wallet.config'].search([('company_id','=',request.env.company.id)], limit=1)
        wallet_balance = self._compute_wallet_balance(partner, wallet_config)

        if not wallet_config:
            raise APIError(status="REJECTED", status_code=500,
                           message="Journal configuration missing for customer wallet")
        if vals.get("wallet_order_id", False) and vals.get("wallet_transaction_ref_id", False):
            wallet_entry = request.env['account.move'].search(
                [('wallet_order_id', '=', vals.get("wallet_order_id", False)),
                 ('wallet_transaction_ref_id', '=', vals.get("wallet_transaction_ref_id", False)),
                 ('state', '=', 'posted'),
                 ('order_transaction_no', '=', vals.get("order_transaction_no", False))])

            if wallet_entry:
                return {
                    'wallet_id': wallet_id,
                    'erp_wallet_trans_ref_id': wallet_entry.name or False,
                    'transaction_ref_id': transaction_ref_id,
                    'order_id': order_id,
                    'balance': wallet_balance,
                    'status_code': 200,
                    'status': "SUCCESS",
                    'msg': "Successfully placed order with wallet amount",
                }

        if wallet_balance < amount:
            raise APIError(status="REJECTED", status_code=402, message="Insufficient wallet balance")

        account_move = self._create_account_move(wallet_config, partner, order_id, amount,vals)
        wallet_balance = self._compute_wallet_balance(partner, wallet_config)
        if account_move:
            return {
                'wallet_id': wallet_id,
                'erp_wallet_trans_ref_id': account_move.name,
                'transaction_ref_id': transaction_ref_id,
                'order_id': order_id,
                'balance': wallet_balance,
                'status_code': 200,
                'status': "SUCCESS",
                'msg': "Successfully placed order with wallet amount"
            }

    def _compute_wallet_balance(self, partner, wallet_config):
        """Compute the current wallet balance."""
        return request.env['res.partner'].compute_wallet_balance(partner, wallet_config,
                                                                        fields.Date.context_today(partner))

    def _create_account_move(self, wallet_config, partner, order_id, amount,vals):
        """Create and post account move for wallet deduction."""
        try:
            service_type = request.env['partner.service.type'].search([('is_delivery_service','=',True),('company_id','=',request.env.company.id)],limit=1)
            move_vals = {
                'partner_id' : partner.id,
                'journal_id': wallet_config.journal_id.id,
                'date' : vals['date'],
                'company_id': request.env.user.company_id.id,
                'currency_id': request.env.user.company_id.currency_id.id,
                'move_type': "entry",
                'service_type_id': service_type.id,
                'order_transaction_no':vals.get('order_transaction_no'),
                'wallet_transaction_ref_id':vals.get('wallet_transaction_ref_id'),
                'wallet_order_id':vals.get('wallet_order_id'),
                'ref':vals.get('ref'),
                'line_ids': [
                    (0, 0, {
                        'partner_id': partner.id,
                        'account_id': wallet_config.default_credit_account_id.id,
                        'credit': 0.0,
                        'debit': amount,
                        'journal_id': wallet_config.journal_id.id,
                        'name': 'Deducted',
                        'wallet_order_id': order_id
                    }),
                    (0, 0, {
                        'partner_id': partner.id,
                        'account_id': wallet_config.wallet_inter_account_id.id,
                        'credit': amount,
                        'debit': 0.0,
                        'journal_id': wallet_config.journal_id.id,
                        'name': 'Deducted',
                        'wallet_order_id': order_id
                    })
                ]
            }
            account_move = request.env['account.move'].create(move_vals)
            account_move.post()
            return account_move
        except Exception as e:
            if e.pgcode == "40001":
                err_msg = str(sys.exc_info()[1])
                raise APIError(status="REJECTED", status_code=409, message=err_msg)
            else:
                try:
                    wallet_entry = self.env['account.move'].search(
                        [('wallet_order_id', '=', vals.get("wallet_order_id", False)),
                         ('wallet_transaction_ref_id', '=', vals.get("wallet_transaction_ref_id", False)),
                         ('state', '=', 'posted'),
                         ('order_transaction_no', '=', vals.get("order_transaction_no", False))])
                    if wallet_entry:
                        return wallet_entry
                except Exception as e:
                    err_msg = str(sys.exc_info()[1])
                    if e.pgcode == "40001" or e.pgcode == "25P02":
                        raise APIError(status="REJECTED", status_code=409, message=err_msg)
                    else:
                        raise APIError(status="REJECTED", status_code=500, message=err_msg)





