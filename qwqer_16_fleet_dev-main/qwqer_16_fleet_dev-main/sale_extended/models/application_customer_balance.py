from odoo import models, fields, _
from datetime import datetime
from odoo.exceptions import ValidationError
import requests
import logging

_logger = logging.getLogger(__name__)


class ApplicationCustomerBalance(models.Model):
    _name = 'application.customer.balance'
    _rec_name = "cus_id"
    _description = 'Application customer balance'
    _order = 'id,time_balance_update desc'

    partner_id = fields.Many2one('res.partner', string='Partner', index=True)
    cus_id = fields.Integer("Customer ID")
    time_balance_update = fields.Datetime("Time of Balance Update")
    company_id = fields.Many2one(related='partner_id.company_id', string='Company', store=True)

    def action_update_customer_balance(self, company_id=None):
        cus_bal_auth = company_id and company_id.customer_balance_sync_api_auth or  self.env.company.customer_balance_sync_api_auth
        cus_bal_url = company_id and company_id.customer_balance_sync_api_url or  self.env.company.customer_balance_sync_api_url
        limit_val = company_id and company_id.customer_balance_sync_api_limit or  self.env.company.customer_balance_sync_api_limit

        if not (cus_bal_auth and cus_bal_url and limit_val):
            raise ValidationError(_("Missing configuration for Customer Balance API."))

        if len(self) > limit_val:
            raise ValidationError(_("Selected records should not exceed the limit of %s.") % limit_val)
        if len(self.mapped('partner_id.company_id')) > 1:
            raise ValidationError(_("Selected records should be from one company. Please select single company") % limit_val)
        partner_ids = self.mapped('partner_id')
        if not partner_ids:
            _logger.info("No partner IDs found for the selected records.")
            return

        partner_balances = self.get_customer_closing_balance(partner_ids.ids)
        if not partner_balances:
            _logger.info("No balances fetched for the provided partners.")
            return

        payload = {"params": []}
        headers = {'Authorization': cus_bal_auth, 'Content-Type': "application/json"}

        for balance in partner_balances:
            rec_ids = self.filtered(lambda rec: rec.partner_id.customer_ref_key == balance['partner_id'])
            rec_id = max(rec_ids, key=lambda rec: rec.id, default=None) if rec_ids else None

            payload["params"].append({
                "customer_id": int(balance['partner_id']),
                "amount": balance['balance'],
                "last_updated_at": str(rec_id.time_balance_update) if rec_id and rec_id.time_balance_update else str(
                    datetime.now())
            })

        try:
            response = requests.post(cus_bal_url, json=payload, headers=headers)
            response_data = response.json()

            if response.status_code == 200 and response_data.get('data', {}).get('success'):
                _logger.info("Customer Balance API successful: %s", response_data)
                processed_partner_ids = response_data['data']['success']
                unlink_records = self.filtered(lambda rec: rec.partner_id.customer_ref_key in processed_partner_ids)

                if unlink_records:
                    unlink_ids = unlink_records.ids
                    _logger.info("Deleting processed records: %s", unlink_ids)
                    query = "DELETE FROM application_customer_balance WHERE id IN %s"
                    self.env.cr.execute(query, (tuple(unlink_ids),))
            else:
                _logger.error("Customer Balance API error: %s", response_data)

        except Exception as e:
            _logger.exception("An error occurred while processing the Customer Balance API.")

    def update_customer_balance(self):
        companies = self.env['res.company'].sudo().search([])
        for company in companies:
            cus_bal_auth = company.customer_balance_sync_api_auth
            cus_bal_url = company.customer_balance_sync_api_url
            limit_val = company.customer_balance_sync_api_limit

            if (cus_bal_auth and cus_bal_url and limit_val):
                data_vals = self.env['application.customer.balance'].search(
                    [('partner_id.company_id', '=', company.id)], limit=limit_val)
                if data_vals:
                    data_vals.action_update_customer_balance(company)
            else:
                _logger.info("Missing configuration for Customer Balance API.")



    def get_customer_closing_balance(self, partner_ids):
        partner_id_condition = "RP.id IN %s"
        params = (tuple(partner_ids),)

        if len(partner_ids) == 1:
            partner_id_condition = "RP.id = %s"
            params = (partner_ids[0],)

        sql = f"""
            SELECT 
                RP.customer_ref_key AS partner_id,
                COALESCE(SUM(AML.balance), 0.00) AS rp_balance,
                COALESCE(SUM(SO.amount_total), 0.00) AS amount_total,
                COALESCE(SUM(DAML.daml_balance), 0.00) AS daml_balance,
                COALESCE(SUM(WAL.wal_balance), 0.00) AS wal_balance,
                COALESCE(SUM(AML.balance), 0.00) + COALESCE(SUM(SO.amount_total), 0.00) +
                COALESCE(SUM(DAML.daml_balance), 0.00) - COALESCE(SUM(WAL.wal_balance), 0.00) AS balance 
            FROM res_partner RP
             JOIN 
                    partner_service_type pst ON pst.id = RP.service_type_id
            LEFT JOIN (
                SELECT 
                    aml.partner_id AS partner_id,
                    COALESCE(SUM(aml.balance), 0.00) AS balance
                FROM account_move_line aml
                JOIN 
                    account_account aa ON aa.id = aml.account_id
                WHERE aa.account_type IN ('asset_receivable', 'liability_payable')
                AND aml.parent_state = 'posted'
                GROUP BY aml.partner_id
            ) AS AML ON (RP.id = AML.partner_id)
            LEFT JOIN (
                SELECT 
                    so.partner_id AS partner_id,
                    COALESCE(SUM(so.amount_total), 0.00) AS amount_total
                FROM sale_order so
                WHERE so.invoice_status = 'to invoice'
                GROUP BY so.partner_id
            ) AS SO ON (RP.id = SO.partner_id)
            LEFT JOIN (
                SELECT 
                    aml.partner_id AS partner_id,
                    COALESCE(SUM(aml.balance), 0.00) AS daml_balance
                FROM account_move_line aml
                JOIN 
                    account_account aa ON aa.id = aml.account_id
                LEFT JOIN account_move am ON (aml.move_id = am.id)
                LEFT JOIN payment_mode pm ON (am.payment_mode_id = pm.id)
                WHERE aa.account_type IN ('liability_payable', 'asset_receivable')
                AND aml.parent_state = 'draft'
                AND aml.partner_id IS NOT NULL
                AND am.line_count > 0.0
                AND pm.is_credit_payment = true
                GROUP BY aml.partner_id
            ) AS DAML ON (RP.id = DAML.partner_id)
            LEFT JOIN (
                SELECT 
                    aml.partner_id AS partner_id,
                    COALESCE(SUM(aml.balance), 0.00) * -1 AS wal_balance
                FROM account_move_line aml
                WHERE aml.parent_state = 'posted'
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
                GROUP BY aml.partner_id
            ) AS WAL ON (RP.id = WAL.partner_id)
            WHERE RP.customer_rank > 0 
            AND RP.active = true 
            AND RP.customer_type = 'b2b' 
            AND pst.is_delivery_service = TRUE
            AND {partner_id_condition}
            GROUP BY RP.id, AML.balance, SO.amount_total, DAML.daml_balance, WAL.wal_balance
        """

        self.env.cr.execute(sql, params)
        partner_balance = self.env.cr.dictfetchall()
        return partner_balance


