# -*- coding: utf-8 -*-
import binascii
import logging
import tempfile

_logger = logging.getLogger(__name__)

from odoo import models, fields
from datetime import datetime, timedelta
import pandas as pd
import logging
from io import BytesIO

_logger = logging.getLogger(__name__)

class AgedBalanceUpdateWizard(models.TransientModel):
    _name = "aged.balance.update.wizard"

    aged_partner_file = fields.Binary(string="Upload File")
    aged_partner_file_name = fields.Char(string="Upload File Name")
    journal_id = fields.Many2one(comodel_name="account.journal", string='Journal')

    def create_journal_entries_from_excel(self, journal_id=1):
        """
        Reads an Excel file and creates journal entries in Odoo.

        Args:
            journal_id (int): ID of the journal to use.
        """
        try:
            file_string = tempfile.NamedTemporaryFile(suffix=".xlsx")
            file_string.write(binascii.a2b_base64(self.aged_partner_file))
            df = pd.read_excel(file_string)
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")

        # Iterate through each row to create journal entries
        for _, row in df.iterrows():
            try:
                # Fetch partner based on Customer ID
                partner = self.env['res.partner'].search([('customer_ref_key', '=', str(row['Customer ID']))], limit=1)
                if not partner:
                    _logger.warning(f"Partner not found for Customer ID: {row['Customer ID']}")
                    continue  # Skip if no partner found

                # Fetch account based on Account Code (if applicable)
                account_id = self.env['account.account'].search([('code', '=', str(row.get('Account Code', '')))],
                                                                limit=1)
                offset_account = self.env['account.account'].search(
                    [('code', '=', '999999')],
                    limit=1)
                if not account_id:
                    continue  # Skip if no account found

                # Define accounting date
                accounting_date = datetime.now().date()

                # Collect aged amounts
                aged_periods = {
                    'Current': row.get('Current', 0.0),
                    '30': row.get('Age ≤ 30 d.', 0.0),
                    '60': row.get('Age ≤ 60 d.', 0.0),
                    '90': row.get('Age ≤ 90 d.', 0.0),
                    '120': row.get('Age ≤ 120 d.', 0.0),
                    '121': row.get('Older', 0.0),
                }

                # Create journal lines for each aged period
                lines = []
                for age, amount in aged_periods.items():
                    if amount == 0 or pd.isna(amount):
                        continue

                    # Calculate due date
                    due_date = accounting_date - timedelta(days=int(age)) if age.isdigit() else accounting_date

                    # Create debit and credit lines
                    lines.append((0, 0, {
                        'account_id': account_id.id,
                        'partner_id': partner.id,
                        'name': f'Debit for {age} days',
                        'debit': amount if amount > 0 else 0.0,
                        'credit': abs(amount) if amount < 0 else 0.0,
                        'date_maturity': due_date,
                    }))
                    lines.append((0, 0, {
                        'account_id': offset_account.id,  # Replace with appropriate credit account ID
                        'partner_id': partner.id,
                        'name': f'Credit for {age} days',
                        'debit': abs(amount) if amount < 0 else 0.0,
                        'credit': amount if amount > 0 else 0.0,
                        'date_maturity': due_date,
                    }))

                # Skip if no valid lines
                if not lines:
                    continue

                # Create the journal entry
                self.env['account.move'].create({
                    'journal_id': journal_id or self.journal_id.id,
                    'date': accounting_date,
                    'ref': f"Aged Partner Balance for {partner.name}",
                    'line_ids': lines,
                })
            except Exception as e:
                # Log the error and continue with the next row
                _logger.error(f"Error processing row {row}: {e}")
                continue

