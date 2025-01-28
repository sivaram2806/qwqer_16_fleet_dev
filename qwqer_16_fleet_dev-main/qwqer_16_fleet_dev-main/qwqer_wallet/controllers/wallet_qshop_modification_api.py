import logging
from datetime import datetime
from odoo import http, fields
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError
import json

_logger = logging.getLogger(__name__)


class WalletQshopModificationAPI(http.Controller):
    @http.route('/wallet/qshop/modification', type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def wallet_modification(self, api_raw_log=None, **kwargs):
        """API to modify the wallet amount deduction"""
        try:
            _logger.info("QShop Wallet Modification Service API : Request Received, Processing ...... ")

            if not kwargs:
                raise APIError(status="REJECTED", status_code=500, message="No Data Received or Incorrect Data Format!")

            params = {k: (False if v is None else v) for k, v in kwargs.items()}
            _logger.info("QShop Wallet Modification Service API : Validating the request ...... ")
            self._validate_request(params)
            _logger.info("QShop Wallet Modification Service API : Request Validated ...... ")
            _logger.info("QShop Wallet Modification Service API : Modification of Wallet Processing ...... ")
            response = self._process_wallet_modification(params)
            api_raw_log.update({
                "response": json.dumps(response),
                'response_date': fields.Datetime.now(),
                'name': "Partner Wallet Deduction",
                'key': params['wallet_id'],
                'status': response['status']
            })
            return json.dumps(response)


        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name="Wallet Modification Api")
        except Exception as e:
            _logger.error(f"Wallet Modification API : Unexpected Error - {str(e)}")
            error = APIError(status="error", status_code=500,
                             message="An unexpected error occurred. Please try again later")
            return error.to_response(api_raw_log=api_raw_log, name="Wallet Modification Api")

    def _validate_request(self, params):
        """Validate mandatory request parameters."""
        required_params = {
            'wallet_id': "Wallet ID",
            'order_id': "Order ID",
            'erp_wallet_trans_id': "ERP Wallet Transaction Ref ID",
            'transaction_ref_id': "Transaction Reference ID",
            'is_delivery_amount_changed': "Is Delivery Amount Changed",
            'is_merchant_amount_changed': "Is Merchant Amount Changed",
            'delivery_amount': "Delivery Amount",
            'merchant_amount': "Merchant Amount"
        }

        for key, desc in required_params.items():
            if key not in params or params[key] in [None, False, ""]:
                _logger.info(f"Wallet Modification API : Mandatory Parameter {desc} Missing.")
                raise APIError(status="REJECTED", status_code=402, message=f"Mandatory Parameter {desc} Missing")

        self._validate_boolean_field(params['is_delivery_amount_changed'], "Is Delivery Amount Changed")
        self._validate_boolean_field(params['is_merchant_amount_changed'], "Is Merchant Amount Changed")

        delivery_amount = float(params['delivery_amount'])
        merchant_amount = float(params['merchant_amount'])

        if params['is_delivery_amount_changed'].lower() == 't' and delivery_amount < 0.00:
            _logger.info("Wallet Modification API : Delivery Amount must be greater than or equal to 0.")
            raise APIError(status="REJECTED", status_code=402,
                           message="Delivery Amount must be greater than or equal to 0")

        if params['is_merchant_amount_changed'].lower() == 't' and merchant_amount < 0.00:
            _logger.info("Wallet Modification API : Merchant Amount must be greater than or equal to 0.")
            raise APIError(status="REJECTED", status_code=402,
                           message="Merchant Amount must be greater than or equal to 0")

    def _validate_boolean_field(self, value, field_name):
        """Validate that a field has a boolean-like value of 'T' or 'F'."""
        if value.lower() not in ['t', 'f']:
            _logger.info(f"Wallet Modification API : {field_name} must be 'T' or 'F'.")
            raise APIError(status="REJECTED", status_code=402, message=f"{field_name} must be 'T' or 'F'.")

    def _process_wallet_modification(self, params):
        """Perform wallet modification process."""
        vals = {}
        account_move = request.env['account.move']
        partner_id = request.env['res.partner'].search([('wallet_id', '=', params.get('wallet_id'))])
        if not partner_id:
            _logger.debug("Wallet Pay Amount Service API : Missing partner for wallet ID %s", params.get('wallet_id'))

            raise APIError(
                status="REJECTED",
                status_code=500,
                message="Missing partner with wallet ID",
                additional_params={'wallet_id': params.get('wallet_id')}
            )
        else:
            if len(partner_id) > 1:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message="Duplicate Customer exists with the same wallet ID",
                    additional_params={'wallet_id': params.get('wallet_id')}
                )
            if not partner_id.is_wallet_active:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message="Customer Wallet is not active",
                    additional_params={'wallet_id': params.get('wallet_id')}
                )
            else:
                vals.update({'partner_id': partner_id.id or False})
        if 'order_id' in params:
            vals.update({'wallet_order_id': params.get('order_id', False) or False})
            vals.update({'ref': "Modified Order - " + params.get('order_id', False) or False})
            # checking order_id already existing or not
            sale_order_exist = request.env['sale.order'].search(
                [('order_id', '=', params.get('order_id', False))])
            if sale_order_exist:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message="Sale order already exist with the order id",
                    additional_params={'wallet_id': params.get('wallet_id'), 'order_id': params.get('order_id')}
                )
        if 'transaction_ref_id' in params:
            vals.update(
                {'wallet_transaction_ref_id': params.get('transaction_ref_id') or False})
            vals.update(
                {
                    'order_transaction_no': "MWD_" + params.get('transaction_ref_id') or False})
            # check_transaction_ref is unique
            move = account_move.search(
                [('wallet_transaction_ref_id', '=', vals.get("wallet_transaction_ref_id", False))])
            if move:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message="Transaction Ref must be Unique",
                    additional_params={'wallet_id': params.get('wallet_id'), 'order_id': params.get('order_id')}
                )
        is_delivery_amount_changed = False
        is_merchant_amount_changed = False
        if 'is_delivery_amount_changed' in params:
            if params.get('is_delivery_amount_changed').lower() == 't':
                is_delivery_amount_changed = True
            else:
                is_delivery_amount_changed = False
        if 'is_merchant_amount_changed' in params:
            if params.get('is_merchant_amount_changed').lower() == 't':
                is_merchant_amount_changed = True
            else:
                is_merchant_amount_changed = False
        reverse_entry = []
        is_merch_amount_reverse_entry_created = False
        is_amount_reverse_entry_created = False
        if 'erp_wallet_trans_id' in params:
            transaction_ref_id = params.get('transaction_ref_id')
            erp_wallet_trans_id = params.get('erp_wallet_trans_id')
            # fetch the journal entry by wallet_order_id and erp_wallet_trans_id
            customer_wallet_entry = account_move.search(
                [('partner_id', '=', vals.get("partner_id", False)),
                 ('wallet_order_id', '=', params.get("order_id", False)),
                 ('name', '=', params.get("erp_wallet_trans_id", False)),
                 ('is_wallet_merchant_journal', '=', False),
                 ('state', '=', 'posted')
                 ])
            if customer_wallet_entry:
                try:
                    if is_delivery_amount_changed:
                        if not customer_wallet_entry.has_reconciled_entries:
                            if customer_wallet_entry.amount_total_signed > 0.0:
                                customer_reverse_entry = customer_wallet_entry.reverse_shop_wallet_entry(
                                    transaction_ref_id)
                                if customer_reverse_entry:
                                    is_amount_reverse_entry_created = True
                                    reverse_entry.append(customer_reverse_entry)
                                    _logger.info("Customer Reverse Entry created %s",
                                                 customer_reverse_entry.id)
                            else:
                                un_reconcile_wallet_entries = account_move.search([
                                    ('partner_id', '=', vals.get("partner_id", False)),
                                    ('wallet_order_id', '=', params.get("order_id", False)),
                                    ('is_wallet_merchant_journal', '=', False), ('state', '=', 'posted'),
                                    ('has_reconciled_entries', '=', False), ('amount_total_signed', '>', 0.0)
                                ])
                                un_reconcile_wallet_entry = un_reconcile_wallet_entries.filtered(
                                    lambda s: not s.has_reconciled_entries)
                                if un_reconcile_wallet_entry:
                                    customer_reverse_entry = un_reconcile_wallet_entry.reverse_shop_wallet_entry(
                                        transaction_ref_id)
                                    if customer_reverse_entry:
                                        is_amount_reverse_entry_created = True
                                        reverse_entry.append(customer_reverse_entry)
                                        _logger.info("Customer Reverse Entry created %s",
                                                     customer_reverse_entry.id)
                                else:
                                    is_amount_reverse_entry_created = True
                        elif customer_wallet_entry and customer_wallet_entry.has_reconciled_entries == True:
                            raise APIError(
                                status="REJECTED",
                                status_code=500,
                                message="Already Modified the Entry",
                                additional_params={'wallet_id': params.get('wallet_id'),
                                                   'transaction_ref_id': params.get('transaction_ref_id'),
                                                   'order_id': params.get('order_id')})
                        else:
                            _logger.info(
                                "Wallet Modification Service API : No entry found "
                                "for this erp wallet transaction Id :%s",
                                params.get("erp_wallet_trans_id"))
                            raise APIError(
                                status="REJECTED",
                                status_code=500,
                                message=f"{params.get('erp_wallet_trans_id')} not found",
                                additional_params={'wallet_id': params.get('wallet_id'),
                                                   'order_id': params.get('order_id')})

                    if is_merchant_amount_changed:
                        # find the merchant journal for reversing
                        merchant_wallet_entries = account_move.search([
                            ('partner_id', '=', vals.get("partner_id", False)),
                            ('wallet_order_id', '=', params.get("order_id", False)),
                            ('is_wallet_merchant_journal', '=', True), ('has_reconciled_entries', '=', False),
                            ('state', '=', 'posted')
                        ])
                        if merchant_wallet_entries:
                            # find un reconciled entry to reverse the entry
                            un_reconcile_merch_wallet_entry = merchant_wallet_entries.filtered(
                                lambda s: not s.has_reconciled_entries)
                            if not un_reconcile_merch_wallet_entry:
                                raise APIError(
                                    status="REJECTED",
                                    status_code=500,
                                    message="Can't Find any Unreconciled entry",
                                    additional_params={'wallet_id': params.get('wallet_id'),
                                                       'order_id': params.get('order_id'),
                                                       'transaction_ref_id': params.get('transaction_ref_id')})

                            else:
                                merchant_reverse_entry = un_reconcile_merch_wallet_entry.reverse_shop_merchant_wallet_entry(
                                    transaction_ref_id)
                                if merchant_reverse_entry:
                                    is_merch_amount_reverse_entry_created = True
                                    reverse_entry.append(merchant_reverse_entry)
                                    _logger.info("Merchant Reverse Entry created %s",
                                                 merchant_reverse_entry.id)
                        else:
                            for entry in reverse_entry:
                                entry.button_draft()
                                entry.button_cancel()
                            _logger.info(
                                "Wallet Modification Service API : No Merchant Entry found for this order Id :%s",
                                params.get("erp_wallet_trans_id"))
                            raise APIError(
                                status="REJECTED",
                                status_code=500,
                                message=f"No Merchant Journal Entry found for the order id {params.get('order_id')}",
                                additional_params={'wallet_id': params.get('wallet_id'),
                                                   'order_id': params.get('order_id'),
                                                   'transaction_ref_id': params.get('transaction_ref_id')})
                except Exception as e:
                    raise APIError(
                        status="REJECTED",
                        status_code=500,
                        message=str(e),
                        additional_params={'wallet_id': params.get('wallet_id'),
                                           'order_id': params.get('order_id')})
            else:
                _logger.info(
                    "Wallet Modification Service API : Entry not found "
                    "for this erp wallet transaction Id :%s",
                    params.get("erp_wallet_trans_id"))
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message=f"{params.get('erp_wallet_trans_id')} not found for the given wallet Id with order ID {params.get('order_id')}",
                    additional_params={'wallet_id': params.get('wallet_id'),
                                       'order_id': params.get('order_id')})

        pay_amount = 0.0
        wallet_bal = 0.0
        merchant_amount = 0.0

        amount = params.get('amount')

        if 'delivery_amount' in params:
            amount = float(params.get('delivery_amount', 0.0))
            if is_delivery_amount_changed:
                pay_amount += amount
        merchant_payment_mode = False
        if merchant_payment_mode in params and params.get('merchant_payment_mode', False):
            merchant_payment_mode = params.get('merchant_payment_mode', False)
        else:
            merchant_payment_mode = 6

        mode_val = request.env['payment.mode'].search([('code', '=', merchant_payment_mode)])
        is_wallet_payment_mode = mode_val.is_wallet_payment
        if is_wallet_payment_mode:
            if 'merchant_amount' in params:
                merchant_amount = float(params.get('merchant_amount', 0.0))
                if is_merchant_amount_changed:
                    pay_amount += merchant_amount
        wallet_config = request.env['customer.wallet.config'].search([('company_id','=',request.env.company.id)], limit=1)
        if not wallet_config:
            _logger.info("Wallet Pay Amount Service API : Journal configuration missing for customer wallet")
            raise APIError(
                status="REJECTED",
                status_code=500,
                message="Journal configuration missing for customer wallet",
                additional_params={'wallet_id': params.get('wallet_id'),
                                   'order_id': params.get('order_id')})
        else:
            # checking customer wallet balance
            try:
                wallet_bal = request.env['res.partner'].compute_wallet_balance(partner_id, wallet_config,
                                                                                      fields.Date.context_today(
                                                                                          partner_id))
            except Exception as e:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message=str(e),
                    additional_params={'wallet_id': params.get('wallet_id'),
                                       'balance': wallet_bal})

            service_type = request.env['partner.service.type'].search(
                [('is_qshop_service', '=', True), ('company_id', '=', request.env.company.id)], limit=1)
            if service_type:
                vals.update({
                    'journal_id': wallet_config.journal_id.id or False,
                    'company_id': request.env.user.company_id.id,
                    'currency_id': request.env.user.company_id.currency_id.id,
                    'move_type': "entry",
                    'service_type_id': service_type.id
                })
            else:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message='Qwqer Shop service Not added')

        if wallet_bal < pay_amount:
            for entry in reverse_entry:
                entry.button_draft()
                entry.button_cancel()
            raise APIError(
                status="REJECTED",
                status_code=500,
                message='Your wallet not having sufficient balance',
                additional_params={'wallet_id': params.get('wallet_id'),
                                   'order_id': params.get('order_id')}
            )
        if is_merchant_amount_changed and is_merch_amount_reverse_entry_created:
            if merchant_amount > 0 and is_wallet_payment_mode:
                if not wallet_config.merchant_inter_account_id:
                    raise APIError(
                        status="REJECTED",
                        status_code=500,
                        message='Wallet merchant intermediate account not mapped in configuration for customer wallet',
                        additional_params={'wallet_id': params.get('wallet_id'),
                                           'order_id': params.get('order_id')}
                    )
                merchant_val = vals.copy()
                merchant_val.update({'is_wallet_merchant_journal': True,
                                     'order_transaction_no': "MQMWD_" + vals.get('wallet_transaction_ref_id',
                                                                                 False) or False
                                     })
                merchant_val.update({'ref': "Modified Merchant Order - " + params.get('order_id', False) or False})
                merchant_move_line_1 = {
                    'partner_id': partner_id.id,
                    'account_id': wallet_config.default_credit_account_id.id or False,
                    'credit': 0.0,
                    'debit': merchant_amount,
                    'journal_id': wallet_config.journal_id.id or False,
                    'name': 'Merchant Deducted',
                    'wallet_order_id': params.get('order_id', False)
                }

                _merchant_move_line_2 = {
                    'partner_id': partner_id.id,
                    'account_id': wallet_config.merchant_inter_account_id.id,
                    'credit': merchant_amount,
                    'debit': 0.0,
                    'journal_id': wallet_config.journal_id.id,
                    'name': "Merchant Deducted",
                    'wallet_order_id': params.get('order_id', False)
                }
                merchant_val.update(
                    {'line_ids': [(0, 0, merchant_move_line_1), (0, 0, _merchant_move_line_2)]
                     }
                )
                merchant_account_move = False
                try:
                    merchant_account_move = request.env['account.move'].create(merchant_val)
                    merchant_account_move.post()
                    if not is_delivery_amount_changed:
                        wallet_bal = request.env['res.partner'].compute_wallet_balance(partner_id, wallet_config,
                                                                                              fields.Date.context_today(
                                                                                                  partner_id))
                        un_reconcile_wallet_entries = account_move.search([
                            ('partner_id', '=', vals.get("partner_id", False)),
                            ('wallet_order_id', '=', params.get("order_id", False)),
                            ('is_wallet_merchant_journal', '=', False), ('state', '=', 'posted'),
                            ('has_reconciled_entries', '=', False),
                            ('name', '=', params.get("erp_wallet_trans_id", False))
                        ])
                        un_reconcile_wallet_entry = un_reconcile_wallet_entries.filtered(
                            lambda s: not s.has_reconciled_entries)
                        if un_reconcile_wallet_entry:
                            return {
                                'wallet_id': params.get('wallet_id'),
                                'erp_wallet_trans_ref_id': un_reconcile_wallet_entry.name,
                                'transaction_ref_id': params.get('transaction_ref_id', False),
                                'order_id': params.get('order_id'),
                                'balance': wallet_bal,
                                'status_code': 200,
                                'status': "SUCCESS",
                                'msg': "Successfully Modified  order with wallet amount",
                            }
                except Exception as e:
                    for entry in reverse_entry:
                        entry.button_draft()
                        entry.button_cancel()
                    raise APIError(
                        status="REJECTED",
                        status_code=500,
                        message=str(e),
                        additional_params={'wallet_id': params.get('wallet_id')}
                    )
        if is_delivery_amount_changed and is_amount_reverse_entry_created:
            move_line_1 = {
                'partner_id': partner_id.id,
                'account_id': wallet_config.default_credit_account_id.id or False,
                'credit': 0.0,
                'debit': amount,
                'journal_id': wallet_config.journal_id.id or False,
                'name': 'Deducted',
                'wallet_order_id': params.get('order_id', False)
            }

            move_line_2 = {
                'partner_id': partner_id.id,
                'account_id': wallet_config.wallet_inter_account_id.id,
                'credit': amount,
                'debit': 0.0,
                'journal_id': wallet_config.journal_id.id,
                'name': "Deducted",
                'wallet_order_id': params.get('order_id', False)
            }

            vals.update(
                {'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)]
                 }
            )
            try:
                new_entry = account_move.create(vals)
                new_entry.post()
            except Exception as e:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message=str(e),
                    additional_params={'wallet_id': params.get('wallet_id')}
                )
            try:
                wallet_bal = request.env['res.partner'].compute_wallet_balance(partner_id, wallet_config,
                                                                                      fields.Date.context_today(partner_id))
            except Exception as e:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message=str(e),
                    additional_params={'wallet_id': params.get('wallet_id')}
                )

            return {
                'wallet_id': params.get('wallet_id'),
                'erp_wallet_trans_ref_id': new_entry.name or False,
                'transaction_ref_id': params.get('transaction_ref_id', False),
                'order_id': params.get('order_id'),
                'balance': wallet_bal,
                'status_code': 200,
                'status': "SUCCESS",
                'msg': "Successfully Modified Order With wallet amount",
            }
