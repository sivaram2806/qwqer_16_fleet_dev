import json
import logging
from datetime import datetime
from odoo import http, fields
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError

_logger = logging.getLogger(__name__)


class WalletDeductVerifyAPI(http.Controller):
    @http.route('/wallet/enquiry/', type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def verify_deduct(self, api_raw_log=None, **kwargs):
        """API to get deduct happen"""
        try:
            _logger.info("Wallet deduct verify API: Request Received, Processing ...... ")
            wallet_id = kwargs.get('wallet_id',False)
            if not wallet_id:
                _logger.info("Wallet deduct verify API  : Mandatory Parameter Wallet ID Not available.")
                raise APIError(
                    status="REJECTED",
                    status_code=402,
                    message="Mandatory Parameter Wallet ID Missing",
                    additional_params={'wallet_id': 0}
                )
            wallet_transaction_ref_id = kwargs.get('wallet_transaction_ref_id', False)
            if not wallet_transaction_ref_id:
                _logger.info(
                    "Wallet deduct verify API : Mandatory Parameter Transaction Reference ID Not available")
                raise APIError(
                    status="REJECTED",
                    status_code=402,
                    message="Mandatory Parameter Transaction Reference ID Missing",
                    additional_params={'wallet_id': wallet_id}
                )
            if wallet_id and wallet_transaction_ref_id:
                partner = request.env['res.partner'].search([('wallet_id', '=', wallet_id)])
                if not partner:
                    _logger.debug("Wallet Pay Amount Service API : Missing partner for wallet ID %s",
                                  wallet_id)
                    raise APIError(
                        status="REJECTED",
                        status_code=500,
                        message="Missing Partner",
                        additional_params={'wallet_id': wallet_id}
                    )
                else:
                    if not partner.is_wallet_active:
                        _logger.debug("Wallet Pay Amount Service API :Wallet is not active %s",
                                      wallet_id)
                        raise APIError(
                            status="REJECTED",
                            status_code=500,
                            message="customer wallet is not active",
                            additional_params={'wallet_id': wallet_id}
                        )
                    else:
                        response= self.fetch_deduct_data(partner,wallet_id,wallet_transaction_ref_id)
                        api_raw_log.update({
                            'response': json.dumps(response),
                            'response_date': fields.Datetime.now(),
                            'key':  kwargs.get('wallet_id') and str(kwargs.get('wallet_id')),
                            'name': 'Wallet deduct verify API',
                            'status': response['status']
                        })
                        return json.dumps(response)


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

    def fetch_deduct_data(self,partner,wallet_id,wallet_transaction):

        try:
            sql = """
                    SELECT 
                        AM.partner_id as wallet_id,
                        AM.wallet_order_id as order_id,
                        AM.wallet_order_id as wallet_order_id,
                        AM.name as erp_wallet_trans_ref_id,
                        AML.debit as debit_amt,
                        AML.credit as credit_amt,
                        AML.name as label,
                        AML.ref as reference,
                        AML.create_date as create_dt
                    FROM 
                        account_move_line AML  
                        JOIN account_move AM on AML.move_id = AM.id
                        JOIN customer_wallet_config CW on CW.journal_id = AML.journal_id 
                        JOIN account_journal AJ on (CW.journal_id = AJ.id and CW.default_credit_account_id = AML.account_id) 
                    WHERE
                        AM.state = 'posted' AND AM.partner_id = %s AND AM.wallet_transaction_ref_id = %s

                 """
            request.env.cr.execute(sql, (partner.id, wallet_transaction))
            res_data = (request.env.cr.dictfetchall())
            trans_list = [data.update({'create_dt': data['create_dt'].strftime('%Y-%m-%d')}) or data for
                          data in res_data]

            wallet_config = request.env['customer.wallet.config'].search([('company_id','=',request.env.company.id)], limit=1)
            wallet_bal = request.env['res.partner'].compute_wallet_balance(partner,
                                                                               wallet_config,
                                                                               fields.Date.context_today(
                                                                                   partner))
            if bool(trans_list):
                return  ({"wallet_id": wallet_id,
                                   "wallet_transaction_ref_id": wallet_transaction,
                                   "balance": wallet_bal,
                                   "trans_list": trans_list,
                                   "status_code": 200,
                                   "status": "SUCCESS",
                                   "msg": "Wallet Transaction List"
                                   })
            else:
                return ({"wallet_id": wallet_id,
                                   "wallet_transaction_ref_id": wallet_transaction,
                                   "status_code": 500,
                                   "status": "REJECTED",
                                   "msg": "No Wallet Entry Found"
                                   })
        except Exception as e:
            raise APIError(
                status="REJECTED",
                status_code=500,
                message=e,
                additional_params={'wallet_id': wallet_id,'wallet_transaction_ref_id':wallet_transaction}
            )
