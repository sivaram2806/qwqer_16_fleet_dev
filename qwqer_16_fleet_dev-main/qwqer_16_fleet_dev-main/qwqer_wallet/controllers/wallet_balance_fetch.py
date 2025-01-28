import json
import logging
from datetime import datetime
from odoo import http, fields
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError

_logger = logging.getLogger(__name__)


class WalletBalanceFetchAPI(http.Controller):
    @http.route('/wallet/balance/fetch/', type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def fetch_balance(self, api_raw_log=None, **kwargs):
        """API to Fetch the balance"""

        try:
            _logger.info("Wallet Balance Fetch Service API: Request Received, Processing...")
            partner = self._get_partner(kwargs)
            # Ensure only one partner exists
            if len(partner) > 1:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message="Duplicate Customer exists with the same wallet ID",
                    additional_params={'wallet_id': 0}
                )

            # Validate wallet status
            if not partner.is_wallet_active:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message="Customer Wallet is not active",
                    additional_params={'wallet_id': partner.wallet_id}
                )

            # Retrieve wallet configuration
            wallet_config = request.env['customer.wallet.config'].search([('company_id','=',request.env.company.id)], limit=1)
            if not wallet_config:
                _logger.info("Wallet Balance Fetch Service API: Journal configuration missing for customer wallet")
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message="Journal configuration missing for customer wallet",
                    additional_params={'wallet_id': partner.wallet_id}
                )

            # Compute wallet balance
            try:
                wallet_balance = request.env['res.partner'].compute_wallet_balance(
                    partner, wallet_config, fields.Date.context_today(partner)
                )
                response={'wallet_id': partner.wallet_id, 'balance': wallet_balance}
                api_raw_log.update({"response": json.dumps(response),
                                'response_date': fields.Datetime.now(),
                                'name': "Wallet Balance Fetch",
                                'key':  kwargs.get('wallet_id') and str(kwargs.get('wallet_id')),
                                'status': "SUCCESS"})
                return json.dumps(response)
            except Exception as e:
                _logger.error(f"Error while computing wallet balance: {str(e)}")
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message=str(e),
                    additional_params={'wallet_id': partner.wallet_id, 'balance': 0.0}
                )

        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name="Wallet Balance Fetch")
        except Exception as e:
            _logger.error(f"Unexpected error: {str(e)}")
            error = APIError(
                status="error",
                status_code=500,
                message="An unexpected error occurred. Please try again later."
            )
            return error.to_response(api_raw_log=api_raw_log, name="Wallet Balance Fetch")

    def _get_partner(self, kwargs):
        """Retrieve the partner based on wallet_id or customer_phone."""
        wallet_id = kwargs.get('wallet_id')
        customer_phone = kwargs.get('customer_phone')

        if wallet_id:
            partner = request.env['res.partner'].search([('wallet_id', '=', wallet_id),('company_id','=',request.env.company.id)])
        elif customer_phone:
            partner = request.env['res.partner'].search(
                [('phone', '=', customer_phone), ('customer_rank', '>', 0),('company_id','=',request.env.company.id)]
            )
        else:
            _logger.info("Wallet Balance Fetch Service API: Mandatory parameter Wallet ID / Phone Number Missing.")
            raise APIError(
                status="REJECTED",
                status_code=402,
                message="Mandatory Parameter Wallet ID / Phone Number Missing",
                additional_params={'wallet_id': 0}
            )

        if not partner:
            _logger.info("Wallet Balance Fetch Service API: No partner found for the provided parameters.")
            raise APIError(
                status="REJECTED",
                status_code=404,
                message="Customer not found",
                additional_params={'wallet_id': wallet_id or 0}
            )
        return partner
