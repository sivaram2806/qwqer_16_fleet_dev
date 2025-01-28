# coding=utf-8
import logging
import json
from datetime import datetime
from odoo import http, fields, _
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WalletTransactionDetailsProcessor:
    """This is a wrapper class for processing wallet transactions details fetching"""

    def __init__(self, env, partner, wallet_config):
        self.env = env
        self.partner = partner
        self.wallet_config = wallet_config
        self.wallet_id = partner.wallet_id

    def compute_wallet_balances(self, start_date=None, end_date=None):
        try:
            wallet_bal = self._get_wallet_balance(date=None)
            wallet_ope_bal = self._get_wallet_balance(
                (datetime.strptime(start_date, "%Y/%m/%d") + relativedelta(days=-1)).strftime(
                    '%Y-%m-%d 18:30:00')) if start_date else wallet_bal
            wallet_closing_bal = self._get_wallet_balance(
                datetime.strptime(end_date, "%Y/%m/%d").strftime('%Y-%m-%d 18:30:00')) if end_date else wallet_bal
            return wallet_bal, wallet_ope_bal, wallet_closing_bal
        except Exception as e:
            raise ValidationError(_("Failed to compute wallet balance: %s" % str(e)))

    def _get_wallet_balance(self, date):
        if date:
            return self.env['res.partner'].compute_wallet_balance(self.partner, self.wallet_config, date)
        return self.env['res.partner'].compute_wallet_balance(self.partner, self.wallet_config,
                                                                     fields.Date.today(self.env))

    def get_transaction_query(self, start_date=None, end_date=None, limit=None, offset=None):
        base_query = self._base_query()
        filter_query = self._build_date_filter(start_date, end_date)
        pagination = self._apply_pagination(limit, offset)

        return f"""
            SELECT partner_id, order_id, service_type , debit_amt, credit_amt, wallet_balance, create_dt, reference, label
            FROM ({base_query}) as wallet
            {filter_query}
            {pagination}
        """

    def _base_query(self):
        return f"""
            SELECT 
            RES.id as partner_id, 
            AML.wallet_order_id as order_id, 
            ST.name as service_type, 
            SUM(AML.debit) as credit_amt, 
            SUM(AML.credit) as debit_amt, 
            sum(AML.balance) as balance_amt, 
            sum(AML.balance)+ COALESCE((sum(AML.balance) OVER(PARTITION BY AML.partner_id ORDER BY AML.id, AML.partner_id ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)),0) as wallet_balance, 
               CASE WHEN CAST (AML.create_date AS TIME) >= '18:30:00' and CAST (AML.create_date AS TIME) <= '23:59:59'
                    THEN to_char(CAST (CAST (AML.create_date AS DATE) + INTERVAL '1 day' AS DATE), 'YYYY/MM/DD') 
                    ELSE to_char(CAST (AML.create_date AS DATE), 'YYYY/MM/DD') END as create_dt,
            AML.ref as reference, 
            AML.name as label
            FROM res_partner RES 
                 JOIN account_move_line AML ON RES.id = AML.partner_id 
                 JOIN account_move AM on AML.move_id = AM.id 
                 LEFT JOIN  partner_service_type ST ON AML.service_type_id = ST.id
            WHERE AML.parent_state != 'cancel' 
                  AND AML.account_id != {self.wallet_config.default_credit_account_id.id}
                  and AML.move_id in 
                   (select move_id from account_move_line where parent_state != 'cancel' and 
                   account_id = {self.wallet_config.default_credit_account_id.id}
                   and journal_id = {self.wallet_config.journal_id.id} and partner_id = {self.partner.id} order by id) 
            GROUP BY RES.id, AML.id,AM.id,ST.name
            ORDER BY AML.create_date DESC
        """

    def _build_date_filter(self, start_date, end_date):
        conditions = []
        if start_date:
            start_date = datetime.strptime(start_date, "%Y/%m/%d").strftime('%Y/%m/%d')
            conditions.append(f"wallet.create_dt >= '{start_date}'")
        if end_date:
            end_date = datetime.strptime(end_date, "%Y/%m/%d").strftime('%Y/%m/%d')
            conditions.append(f"wallet.create_dt <= '{end_date}'")
        return f"WHERE {' AND '.join(conditions)}" if conditions else ""

    def _apply_pagination(self, limit, offset):
        return f"LIMIT {limit} OFFSET {offset}" if limit and offset is not None else ""

    def execute_query(self, query):
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def get_total_records(self, query):
        count_query = f"SELECT COUNT(*) FROM ({query}) AS total"
        self.env.cr.execute(count_query)
        return self.env.cr.fetchone()[0]


class WalletTransactionDetailsAPI(http.Controller):
    @http.route('/wallet/details/listing', type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def wallet_transaction_listing(self, api_raw_log=None, **kwargs):
        api_name = 'Wallet Transaction Detail Listing'
        wallet_id = kwargs.get('wallet_id')
        try:
            if not kwargs:
                raise APIError(status="REJECTED", status_code=500, message="No Data Received or Incorrect Data Format")
            missing_fields = []

            if not kwargs.get('wallet_id'):
                missing_fields.append('wallet_id')
            if not (kwargs.get('start_date') or kwargs.get('end_date')):
                missing_fields.extend(['start_date','end_date'])

            if missing_fields:
                raise APIError(status="REJECTED", status_code=402,
                               message=f"Mandatory fields missing: {', '.join(missing_fields)}")

            partner = request.env['res.partner'].search([('wallet_id', '=', wallet_id)])
            if not partner:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message=f"Missing partner for wallet ID {wallet_id}.",
                    additional_params={'wallet_id': wallet_id}
                )
            if not partner.is_wallet_active:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message="Customer wallet is not active.",
                    additional_params={'wallet_id': wallet_id}
                )

            # Validate wallet configuration
            wallet_config = request.env['customer.wallet.config'].search([('company_id', '=', request.env.company.id)],
                                                                         limit=1)
            if not wallet_config:
                raise APIError(
                    status="REJECTED",
                    status_code=500,
                    message="Journal configuration missing for customer wallet",
                    additional_params={'wallet_id': wallet_id}
                )
            else:
                processor = WalletTransactionDetailsProcessor(request.env, partner, wallet_config)

                start_date = kwargs.get('start_date')
                end_date = kwargs.get('end_date')
                limit = kwargs.get('limit')
                offset = kwargs.get('offset')

                wallet_bal, wallet_ope_bal, wallet_closing_bal = processor.compute_wallet_balances(start_date, end_date)

                # Generate SQL Query
                transaction_query = processor.get_transaction_query(start_date, end_date, limit, offset)

                # Fetch total records
                total_records = processor.get_total_records(transaction_query)

                # Fetch paginated data
                transactions = processor.execute_query(transaction_query)

                response = {
                    'wallet_id': partner.wallet_id,
                    'wallet_ope_bal': wallet_ope_bal,
                    'wallet_closing_bal': wallet_closing_bal,
                    'current_balance': wallet_bal,
                    'trans_list': transactions,
                    'total_records': total_records,
                    'status_code': 200,
                    'status': "SUCCESS",
                }
                api_raw_log.update({
                    'name': api_name,
                    'key': wallet_id,
                    "response": json.dumps(response),
                    'response_date': fields.Datetime.now(),
                    'status': response.get('status')
                })
            return json.dumps(response)
        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name=api_name)
        except Exception as e:
            msg = str(e)
            _logger.error(f"Unexpected error: {msg}")
            error = APIError(status="REJECTED", status_code=500, message=msg,
                             additional_params={'wallet_id': wallet_id})
            return error.to_response(api_raw_log=api_raw_log, name=api_name)
