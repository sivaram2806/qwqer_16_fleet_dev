import logging
import json
from datetime import datetime
import pytz
from odoo import http, fields
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError
from psycopg2.errors import UniqueViolation


_logger = logging.getLogger(__name__)


class WalletRechargeAPI(http.Controller):
    @http.route('/wallet/recharge', type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def recharge_wallet(self, api_raw_log=None, **kwargs):
        """API to recharge customer wallet"""

        try:
            customer_phone = kwargs.get('customer_phone')
            amount = float(kwargs.get('amount', 0))
            transaction_ref_id = kwargs.get('transaction_ref_id')
            transaction_date_val = kwargs.get('transaction_date')
            wallet_id = kwargs.get('wallet_id')
            if not customer_phone:
                _logger.info("Wallet Recharge Service API: Mandatory Parameter Customer Phone Not available.")
                raise APIError(status="REJECTED", status_code=402, message="Mandatory Parameter Customer Phone Missing")

            if amount <= 0:
                _logger.info(
                    "Wallet Recharge Service API: Mandatory Parameter Amount not available or must be greater than 0."
                )
                raise APIError(status="REJECTED", status_code=402,
                               message="Mandatory Parameter Amount missing or must be greater than 0")

            if not transaction_ref_id:
                _logger.info(
                    "Wallet Recharge Service API: Mandatory Parameter Transaction Ref id is missing or Not available"
                )
                raise APIError(status="REJECTED", status_code=402,
                               message="Mandatory Parameter Transaction Ref id is missing or Not available", )

            transaction_date = self._parse_transaction_date(transaction_date_val, customer_phone)
            if isinstance(transaction_date, dict):
                return transaction_date  # Error response from parsing function

            # Process wallet recharge
            response = self.recharge_partner_wallet(wallet_id, customer_phone, amount, transaction_date, kwargs)


            api_raw_log.update({
                "response": json.dumps(response),
                'response_date': fields.Datetime.now(),
                'name': "Partner Wallet Recharge",
                'key': wallet_id,
                'status': response['status']
            })
            return json.dumps(response)

        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name="Wallet Recharge API")
        except Exception as e:
            _logger.error(f"Unexpected error: {str(e)}")
            error = APIError(status="error", status_code=500,
                             message="An unexpected error occurred. Please try again later.")
            return error.to_response(api_raw_log=api_raw_log, name="Wallet Recharge API")

    def recharge_partner_wallet(self, wallet_id, customer_phone, amount, transaction_date, data):
        """Perform wallet recharge by creating a journal entry for the customer"""
        partner = self._find_or_create_partner(wallet_id, customer_phone, data)
        if isinstance(partner, dict):
            return partner  # Error response from partner finding/creation

        wallet_config = request.env['customer.wallet.config'].search([('company_id','=',request.env.company.id)], limit=1)
        if not wallet_config:
            raise APIError(status="REJECTED", status_code=500,
                           message="Journal configuration missing for customer wallet",
                           additional_params={'customer_phone': customer_phone})
        # Prepare journal entry values
        vals = self._prepare_journal_entry_vals(partner, wallet_config, transaction_date, amount, data)
        try:
            account_move = self._create_and_post_journal_entry(vals, partner, data)
        except UniqueViolation as e:
            request.env.cr.rollback()
            err_msg = "Record already exist with Order Transaction Number : " + data['transaction_ref_id']
            return {
                'transaction_ref_id': data['transaction_ref_id'],
                'status_code': 500,
                'status': "REJECTED",
                'msg': err_msg
            }
        except Exception as e:
            raise APIError(status="REJECTED", status_code=500, message=e,
                           additional_params={'customer_phone': customer_phone})

        wallet_bal = partner.compute_wallet_balance(partner, wallet_config,
                                                           fields.Date.context_today(account_move))
        return {
            'erp_wallet_trans_ref_id': account_move.name,
            'wallet_id': partner.wallet_id,
            'customer_phone': customer_phone,
            'wallet_bal': wallet_bal,
            'status_code': 200,
            'status': "SUCCESS",
            'msg': "Wallet recharged successfully"
        }

    def _prepare_journal_entry_vals(self, partner, wallet_config, transaction_date, amount, data):
        """Prepare values for the journal entry"""
        return {
            'partner_id': partner.id,
            'journal_id': wallet_config.journal_id.id,
            'company_id': request.env.user.company_id.id,
            'currency_id': request.env.user.company_id.currency_id.id,
            'move_type': "entry",
            'service_type_id': data.get('service_type_id', False),
            'ref': f"Recharge - {data.get('transaction_ref_id', '')}",
            'wallet_transaction_ref_id': data.get('transaction_ref_id', ''),
            'order_transaction_no': f"WR_{data.get('transaction_ref_id', '')}",
            'date': transaction_date,
            'line_ids': [
                (0, 0, {
                    'partner_id': partner.id,
                    'account_id': wallet_config.wallet_debit_account_id.id,
                    'debit': amount,
                    'credit': 0.0,
                    'journal_id': wallet_config.journal_id.id,
                    'name': 'Recharged'
                }),
                (0, 0, {
                    'partner_id': partner.id,
                    'account_id': wallet_config.default_credit_account_id.id,
                    'debit': 0.0,
                    'credit': amount,
                    'journal_id': wallet_config.journal_id.id,
                    'name': 'Recharged'
                })
            ]
        }

    def _find_or_create_partner(self, wallet_id, customer_phone, data):
        """Find or create a partner based on wallet_id or phone"""
        partner = request.env['res.partner'].search([('wallet_id', '=', wallet_id),('company_id','=',request.env.company.id)]) if wallet_id else None

        if not partner:
            partner = request.env['res.partner'].search([('phone', '=', customer_phone)])

        if not partner and data.get('customer_name') and data.get('region'):
            try:
                region_val = request.env['sales.region'].search([
                    ('region_code', '=', data['region']),
                    ('company_id', '=', request.env.company.id)
                ])
                service_type = False
                if data.get('service_type'):
                    if data.get('service_type') == 'delivery':
                        service_type = request.env['partner.service.type'].search([('is_delivery_service','=',True),('company_id','=',request.env.company.id)],limit=1)
                    else:
                        service_type = request.env['partner.service.type'].search([('is_qshop_service','=',True),('company_id','=',request.env.company.id)],limit=1)

                partner = request.env['res.partner'].create({
                    'name': data['customer_name'],
                    'phone': customer_phone,
                    'customer_type': 'b2c',
                    'service_type_id': service_type.id or False,
                    'state_id': region_val.state_id.id,
                    'region_id': region_val.id,
                    'customer_rank': 1,
                    'is_wallet_active': True
                })
                if partner:
                    partner.wallet_id = partner.customer_ref_key
            except Exception as e:
                raise APIError(status="REJECTED", status_code=500, message=str(e),
                               additional_params={'customer_phone': customer_phone, "wallet_id": partner.wallet_id, })
        # Ensure only one partner exists
        if len(partner) > 1:
            raise APIError(
                status="REJECTED",
                status_code=500,
                message="Duplicate Customer exists with the same wallet ID",
                additional_params={'wallet_id': wallet_id}
            )

        if partner and not partner.is_wallet_active:
            raise APIError(status="REJECTED", status_code=500, message="Customer wallet is not active.",
                           additional_params={'customer_phone': customer_phone})
        return partner

    def _parse_transaction_date(self, transaction_date_val, customer_phone):
        """Parse and validate transaction date"""
        if not transaction_date_val:
            return None

        try:
            local_tz = pytz.timezone(request.env.user.tz or 'UTC')
            tras_dt = datetime.strptime(transaction_date_val, "%Y/%m/%d")
            _logger.info("Wallet Recharge Service API: Transaction Date %s for customer phone %s",
                         tras_dt, customer_phone)
            return local_tz.localize(tras_dt)
        except ValueError:
            raise APIError(status="REJECTED", status_code=402, message="Invalid Transaction Date Format")

    def _create_and_post_journal_entry(self, vals, partner, data):
        """Create and post a journal entry"""
        account_move = request.env['account.move'].search([
            ('partner_id', '=', partner.id),
            ('wallet_transaction_ref_id', '=', data.get('transaction_ref_id', '')),
            ('state', '=', 'posted')
        ])

        if not account_move:
            account_move = request.env['account.move'].create(vals)
            account_move.post()
        return account_move
