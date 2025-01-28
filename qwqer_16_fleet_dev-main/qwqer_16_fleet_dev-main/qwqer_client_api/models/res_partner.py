# -*- coding: utf-8 -*-
import json

import requests

from odoo import models, fields, _
from odoo.exceptions import ValidationError
from odoo.api import model, _logger
from odoo.exceptions import ValidationError, UserError




class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Modified res.partner to add fields'


    def fetch_and_update_customer_balance_from_13(self):
        driver_ids = [partner_id for partner_id in self.mapped('driver_uid') if partner_id]
        partner_ids = [partner_id for partner_id in self.mapped('customer_ref_key') if partner_id]
        if driver_ids or partner_ids:
            driver_balance = self.get_partner_closing_balance(partner_ids, driver_ids)


    def get_partner_closing_balance(self, partner_ids, driver_ids):
        if not partner_ids and not driver_ids:
            raise ValidationError("Please Select atl east one partner to proceed")
        api_credentials = self.env['qwqer.api.credentials'].sudo().search([], limit=1)
        if api_credentials and api_credentials.is_partner_update:
            wallet_balance_date = api_credentials.wallet_sync_date_to
            driver_balance_data = api_credentials.driver_balance_date_to
            headers = {
                'SecretKey': api_credentials.authorization,
                'content-type': "application/json",
            }
            url = api_credentials.server_url + '/api/partner_balances/sync'
            try:
                response = requests.request("POST", url, json={"params": {"partner_ids": partner_ids,
                                                                          "driver_ids": driver_ids,
                                                                          'wallet_balance_date': fields.Date.to_string(wallet_balance_date),
                                                               'driver_balance_date': fields.Date.to_string(driver_balance_data)}},
                                            headers=headers)
                response_data = response.json()['result']
                data = json.loads(response_data).get("data")

                # Define the accounts
                driver_account = api_credentials.driver_account or self.env['account.account'].search([('code', '=', '100241')],
                                                                    limit=1)
                wallet_account = api_credentials.wallet_account or self.env['account.account'].search([('code', '=', '200300')],
                                                                    limit=1)
                offset_account = api_credentials.offset_account or self.env['account.account'].search([('code', '=', '999999')],
                                                                    limit=1)
                # journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
                for rec in data.get('customer_data'):
                    journal = api_credentials.wallet_journal
                    partner_id = self.env["res.partner"].search([("customer_ref_key", "=", rec.get("partner_id"))], limit=1)
                    self.create_opening_journal_entry(partner_id, journal, rec.get("wal_balance"), wallet_account, offset_account,wallet_balance_date)
                for rec in data.get('driver_balance'):
                    journal = api_credentials.driver_balance_journal
                    partner_id = self.env["res.partner"].search([("driver_uid", "=", rec.get("driver_id"))], limit=1)
                    self.create_driver_opening_journal_entry(partner_id, journal, rec.get("balance"), driver_account, offset_account,driver_balance_data)
            except:
                pass

    def create_opening_journal_entry(self, partner_id, journal, balance, main_account, offset_account,wallet_balance_date):
        """
        Creates a journal entry for the opening wallet balance of a partner,
        handling both positive and negative balances.
        """
        if balance == 0:
            return

        # Get the opening balance journal
        if not journal:
            raise ValueError(_("No general journal found. Please configure a general journal."))

        # Prepare journal entry data
        move_vals = {
            'journal_id': journal.id,
            'partner_id': partner_id.id,

            'date': wallet_balance_date,
            'ref': f'Opening Customer Wallet Balance for {partner_id.name}',
            'line_ids': [],
        }

        if balance < 0:
            # Positive balance: Debit Wallet, Credit Offset
            move_vals['line_ids'] = [
                (0, 0, {
                    'account_id': main_account.id,
                    'partner_id': partner_id.id,
                    'name': f'Customer Wallet Balance for {partner_id.name}',
                    'debit': abs(balance),
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': offset_account.id,
                    'partner_id': partner_id.id,
                    'name': 'Offset Entry',
                    'debit': 0.0,
                    'credit': abs(balance),
                }),
            ]
        else:
            # Negative balance: Credit Wallet, Debit Offset
            move_vals['line_ids'] = [
                (0, 0, {
                    'account_id': main_account.id,
                    'partner_id': partner_id.id,
                    'name': f'Customer Wallet Balance for {partner_id.name}',
                    'debit': 0.0,
                    'credit': abs(balance),
                }),
                (0, 0, {
                    'account_id': offset_account.id,
                    'partner_id': partner_id.id,
                    'name': 'Offset Entry',
                    'debit': abs(balance),
                    'credit': 0.0,
                }),
            ]

        # Create and post the journal entry
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        return move

    def create_driver_opening_journal_entry(self, partner_id, journal, balance, main_account, offset_account, driver_balance_data):
        """
        Creates a journal entry for the opening balance of driver,
        handling both positive and negative balances.
        """
        if balance == 0:
            return

        # Get the opening balance journal
        if not journal:
            raise ValueError(_("No general journal found. Please configure a general journal."))

        # Prepare journal entry data
        move_vals = {
            'journal_id': journal.id,
            'partner_id': partner_id.id,

            'date': driver_balance_data,
            'ref': f'Opening Driver Balance for {partner_id.name}',
            'line_ids': [],
        }

        if balance < 0:
            # Positive balance: Debit Balance, Credit Offset
            move_vals['line_ids'] = [
                (0, 0, {
                    'account_id': main_account.id,
                    'partner_id': partner_id.id,
                    'name': f'Driver Balance for {partner_id.name}',
                    'debit': 0.0,
                    'credit': abs(balance),
                }),
                (0, 0, {
                    'account_id': offset_account.id,
                    'partner_id': partner_id.id,
                    'name': 'Offset Entry',
                    'debit': abs(balance),
                    'credit': 0.0,
                }),
            ]
        else:
            # Negative balance: Credit Balance, Debit Offset
            move_vals['line_ids'] = [
                (0, 0, {
                    'account_id': main_account.id,
                    'partner_id': partner_id.id,
                    'name': f'Driver  Balance for {partner_id.name}',
                    'debit': abs(balance),
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': offset_account.id,
            'partner_id': partner_id.id,
                    'name': 'Offset Entry',
                    'debit': 0.0,
                    'credit': abs(balance),
                }),
            ]

        # Create and post the journal entry
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        return move

    def get_partner_age(self):
        api_credentials = self.env['qwqer.api.credentials'].sudo().search([], limit=1)
        url = api_credentials.server_url + '/api/partner_age/sync'
        for rec in self:
            params = {
                'partner_id': rec.customer_ref_key,
            }
            try:
                response = requests.get(url, params=params)
                print(response)
                if response.status_code == 200:
                    # Convert the response from JSON format
                    data = response.json()
                    if data['data']['joining_date']:
                        rec.joining_date = data['data']['joining_date']
                    else:
                        rec.joining_date = rec.create_date

            except Exception as e:
                _logger.info("Error :exception happened : %s", e)
                raise UserError(e)

    def get_partner_ref_key(self):
        api_credentials = self.env['qwqer.api.credentials'].sudo().search([], limit=1)
        url = api_credentials.server_url + '/api/ref_key/sync'
        for rec in self:
            if not rec.customer_ref_key and rec.phone:
                params = {
                    'phone': rec.phone.replace("+91", ""),
                }
                try:
                    response = requests.get(url, params=params)
                    print(response)
                    if response.status_code == 200:
                        # Convert the response from JSON format
                        data = response.json()
                        if data['data']['customer_ref_key']:
                            rec.customer_ref_key = data['data']['customer_ref_key']
                            rec.wallet_id = data['data']['customer_ref_key']

                except Exception as e:
                    _logger.info("Error :exception happened : %s", e)
                    raise UserError(e)
