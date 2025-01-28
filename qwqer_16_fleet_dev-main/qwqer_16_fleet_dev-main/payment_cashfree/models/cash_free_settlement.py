# -*- coding: utf-8 -*-
from odoo import models, fields
import requests
import json
from datetime import datetime, timezone
import logging

_logger = logging.getLogger(__name__)


class CashFreeSettlement(models.Model):
    _name = 'cash.free.settlement'
    _description = 'Cash Free'

    name = fields.Char(string='ID')
    total_transaction_amount = fields.Float(string='Total Transaction Amount')
    settlement_amount = fields.Float(string='Settlement Amount')
    adjustment = fields.Float(string='Adjustment')
    net_settlement_amount = fields.Float(string='Net Settlement Amount')
    service_tax = fields.Float(string='Service Tax')
    service_charge = fields.Float(string='Service Charge')
    from_date = fields.Date(string="From")
    till_date = fields.Date(string="Till")
    utr = fields.Char(string='UTR No.')
    settlement_date = fields.Date(string="Settlement Date")
    journal_id = fields.Many2one("account.journal", string='Journal')
    partner_id = fields.Many2one('res.partner', string='Partner',
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], )
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method', )
    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')],
        string='Payment Type', )
    validated = fields.Boolean(string="validated")
    payment_id = fields.Many2one('account.payment', string='Payment')

    # Company id for Multi-Company property
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    def create_validate_payments(self):
        """
            To create payment records and post,
             update validated status and payment id
        """
        for rec in self:
            if not rec.validated:
                payment = self.env['account.payment'].with_context({'skip_account_move_synchronization': True}).create({
                    'partner_type': rec.partner_type,
                    'partner_id': rec.partner_id.id,
                    'amount': rec.net_settlement_amount,
                    'journal_id': rec.journal_id.id,
                    'payment_type': rec.payment_type,
                    'payment_method_id': rec.payment_method_id.id,
                    'date': rec.settlement_date,
                    'company_id':rec.company_id.id,
                })
                payment.sudo().with_context({'skip_account_move_synchronization': True}).action_post()
                rec.validated = True
                rec.payment_id = payment

    def _cron_cash_free_api_import(self):
        """
            Cron to import cashfree settlements
        """
        for company in self.env['res.company'].search([]):
            self.cash_free_api_import(company.id)

    def cash_free_api_import(self, company_id, api_date=None):
        """
        To call cashfree settlement api and create records for settlement
        @param company_id: 
        @param api_date: from date which the settlement data to be imported
        """
        credential = self.env['cash.free.credentials'].search([("company_id", "=", company_id)], limit=1)
        config = self.env['cash.free.configuration'].search([], limit=1)
        end_date_iso = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
        start_date = datetime.combine(api_date or credential.api_date, datetime.min.time())
        start_date_iso = start_date.replace(tzinfo=None).isoformat() + 'Z'
        if credential:
            url = "	https://api.cashfree.com/pg/settlements"
            payload = {
                "pagination": {"limit": 10},
                "filters": {
                    "start_date": start_date_iso,
                    "end_date": end_date_iso
                }
            }
            headers = {
                "accept": "application/json",
                "x-client-id": credential.name,
                "x-client-secret": credential.key,
                "x-api-version": "2022-09-01",
                "content-type": "application/json"
            }
            response = requests.post(url, headers=headers, json=payload)
            _logger.info(response.text)
            data = json.loads(response.text)
            if not data or not data.get("data"):
                _logger.info(f"No Cashfree settlement data fount for period:{start_date_iso} - {end_date_iso}")
            for rec in data.get("data", []):
                total_tax = float(rec['service_tax']) + float(rec['service_charge'])
                settlement_amount = round(float(rec['payment_amount']) - total_tax, 2)
                exsist = self.env['cash.free.settlement'].search([('name', '=', rec['cf_settlement_id']), ("company_id", "=", company_id)])
                if not exsist:
                    cash_free = self.env['cash.free.settlement'].create({
                        'company_id': company_id,
                        'name': rec['cf_settlement_id'],
                        'total_transaction_amount': rec['payment_amount'],
                        'settlement_amount': settlement_amount,
                        'adjustment': rec['adjustment'],
                        'net_settlement_amount': rec['amount_settled'],
                        'service_tax': rec['service_tax'],
                        'service_charge': rec['service_charge'],
                        # 'net_settlement_amount':rec['amountSettled'],
                        'from_date': rec['payment_from'],
                        'till_date': rec['payment_till'],
                        'utr': rec['settlement_utr'],
                        'settlement_date': rec['settlement_date'],
                        'payment_method_id': config.payment_method_id.id,
                        'payment_type': config.payment_type,
                        'journal_id': config.journal_id.id,
                        'partner_id': config.partner_id.id,
                        'partner_type': config.partner_type,
                    })
                    if config.is_validated:
                        if cash_free.partner_id:
                            cash_free.create_validate_payments()
            # get latest settlement date and update it in credentials api date
            last_settlement = self.env['cash.free.settlement'].search([("company_id", "=", company_id)], limit=1, order='settlement_date desc')
            if last_settlement:
                credential.write({'api_date': last_settlement.settlement_date})
