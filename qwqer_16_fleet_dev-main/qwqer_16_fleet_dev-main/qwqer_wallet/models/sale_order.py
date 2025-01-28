# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.exceptions import UserError
import sys
from datetime import date
from odoo import exceptions


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_wallet_reversed = fields.Boolean("Is wallet reversed")
    wallet_move_id = fields.Many2one(comodel_name='account.move', string="Wallet Transaction", index=True)
    merchant_wallet_move_id = fields.Many2one(comodel_name='account.move', string="Merchant Wallet Transaction")
    wallet_transaction_ref_id = fields.Char(string='Wallet Transaction No')

    # reversing wallet intermediate journal entry
    def reverse_wallet_entry(self):
        wallet_entry = self.wallet_move_id
        wallet_config = self.env['customer.wallet.config'].search([('company_id','=',self.env.company.id)], limit=1)
        if not wallet_config:
            return

        move_lines = wallet_entry.line_ids.filtered(
            lambda r: r.wallet_order_id == self.order_id \
                      and r.account_id == wallet_config.wallet_inter_account_id
        )

        if move_lines and move_lines.full_reconcile_id:
            reconciled_lines = self.env['account.move.line'].search([
                ('full_reconcile_id', '=', move_lines.full_reconcile_id.id),
                ('move_id', '!=', move_lines.move_id.id),
                ('parent_state', '=', 'posted')
            ])
            reconciled_line = reconciled_lines.mapped('move_id.line_ids').filtered(
                lambda r: r.account_id == wallet_config.wallet_round_off_account_id
            )
            move_lines.remove_move_reconcile()

            if reconciled_line:
                reconciled_line.move_id.button_draft()
                reconciled_line.move_id.button_cancel()

        # Prepare values for the reverse entry
        order_transaction_no = _('WRE_%s_%s') % (wallet_entry.wallet_transaction_ref_id, self.order_id)
        ref = _('Cancelled Order - %s') % self.order_id
        partner_id = self.billing_partner_id.id if self.service_type_id.is_qshop_service else self.partner_id.id

        vals = {
            'partner_id': partner_id,
            'selling_partner_id': self.partner_id.id if self.service_type_id.is_qshop_service else False,
            'date': fields.Date.today(),
            'wallet_transaction_ref_id': wallet_entry.wallet_transaction_ref_id,
            'order_transaction_no': order_transaction_no,
            'journal_id': wallet_config.journal_id.id,
            'company_id': self.env.user.company_id.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'move_type': "entry",
            'service_type_id': self.service_type_id.id,
            'ref': ref,
            'line_ids': [
                (0, 0, {
                    'partner_id': partner_id,
                    'account_id': wallet_config.default_credit_account_id.id,
                    'credit': move_lines.credit,
                    'debit': 0.0,
                    'journal_id': wallet_config.journal_id.id,
                    'name': 'Refunded',
                    'wallet_order_id': self.order_id
                }),
                (0, 0, {
                    'partner_id': partner_id,
                    'account_id': wallet_config.wallet_inter_account_id.id,
                    'credit': 0.0,
                    'debit': move_lines.credit,
                    'journal_id': wallet_config.journal_id.id,
                    'name': "Refunded",
                    'wallet_order_id': self.order_id
                })
            ]
        }

        account_move = self.env['account.move'].sudo().create(vals)
        account_move.sudo().post()

        # Reconcile move lines
        move_line_ids = move_lines.filtered(
            lambda r: r.account_id == wallet_config.wallet_inter_account_id
        ).ids + account_move.line_ids.filtered(
            lambda r: r.account_id == wallet_config.wallet_inter_account_id
        ).ids

        if move_line_ids:
            self.env['account.move.line'].browse(move_line_ids).reconcile()

        # Update fields
        self.is_wallet_reversed = True
        self.wallet_move_id = False

    def action_so_list_cancel(self):
        for rec in self:
            rec.reverse_credit_sale_journal()
            rec.reverse_merchant_journal()
            rec.action_cancel()

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        payment_modes = self.env['payment.mode'].search([('is_wallet_payment', '=', True)])
        modes = payment_modes.filtered(lambda st: st.code == res.payment_mode_id.code)
        merchant_payment_mode = payment_modes.filtered(lambda st: st.code == res.merchant_payment_mode_id.code)
        if modes:
            if not res.wallet_move_id:
                moves = self.env['account.move.line'].sudo().search(
                    [('wallet_order_id', '=', res.order_id), ('move_id.is_wallet_merchant_journal', '=', False)])
                res.wallet_move_id = moves.move_id.id
        if merchant_payment_mode:
            if not res.merchant_wallet_move_id and res.order_status_id.code == "4" and res.service_type_id.is_qshop_service:
                moves = self.env['account.move.line'].sudo().search(
                    [('wallet_order_id', '=', res.order_id), ('move_id.is_wallet_merchant_journal', '=', True),
                     ])
                un_reconcile_merch_wallet_entry = moves.filtered(
                    lambda s: not s.move_id.has_reconciled_entries)
                if un_reconcile_merch_wallet_entry:
                    res.merchant_wallet_move_id = un_reconcile_merch_wallet_entry.move_id.id
        res.wallet_transaction_ref_id = res.sudo().wallet_move_id.wallet_transaction_ref_id
        if modes and res.state == 'cancel' and res.wallet_move_id:
            if res.total_amount > 0:
                res.sudo().reverse_wallet_entry()
        return res

    def _create_wallet_merchant_entry(self, wallet_config):
        merchant_vals = {}
        merchant_vals.update({'partner_id': self.billing_partner_id.id or False,
                              'journal_id': wallet_config.journal_id.id or False,
                              'company_id': self.env.user.company_id.id,
                              'currency_id': self.env.user.company_id.currency_id.id,
                              'move_type': "entry",
                              'wallet_order_id': self.order_id or False,
                              'ref': "Merchant Order Delivered - " + self.order_id or False,
                              'service_type_id': self.service_type_id.id,
                              'date': fields.Datetime.now(self).date() or False,
                              'is_wallet_merchant_journal': True,
                              'wallet_transaction_ref_id': self.wallet_transaction_ref_id,
                              'order_transaction_no': "QMWRD_" + self.wallet_transaction_ref_id})
        merchant_move_line_1 = {
            'partner_id': self.billing_partner_id.id,
            'account_id': wallet_config.default_credit_account_id.id or False,
            'credit': 0.0,
            'debit': self.merchant_order_amount,
            'journal_id': wallet_config.journal_id.id or False,
            'wallet_order_id': self.order_id or False,
            'name': 'Merchant Amount Deducted'}
        _merchant_move_line_2 = {
            'partner_id': self.billing_partner_id.id,
            'account_id': wallet_config.merchant_inter_account_id.id,
            'credit': self.merchant_order_amount,
            'debit': 0.0,
            'journal_id': wallet_config.journal_id.id,
            'wallet_order_id': self.order_id or False,
            'name': " Merchant Amount Deducted"}
        merchant_vals.update(
            {'line_ids': [(0, 0, merchant_move_line_1), (0, 0, _merchant_move_line_2)]})
        try:
            merchant_account_move = self.env['account.move'].sudo().create(merchant_vals)
            merchant_account_move.sudo().post()
            self.merchant_wallet_move_id = merchant_account_move.id
        except Exception as e:
            err_msg = str(sys.exc_info()[1])
            raise exceptions.ValidationError(err_msg)  # Creating wallet entry

    def action_update_wallet_transaction(self, vals):
        """
        Update wallet transactions based on the provided values and company-specific context.
        """
        self.ensure_one()

        if self._context.get('from_api', False):
            status = vals.get('state', self.state)
            if not self.payment_mode_id.is_wallet_payment:
                return

            if not self.is_wallet_reversed and self.wallet_move_id and status == 'cancel':
                self.sudo().reverse_wallet_entry()
            elif self._should_create_wallet_entry(vals):
                self._process_wallet_entry(vals, status)
            elif self._should_create_merchant_entry(vals):
                self._process_merchant_entry(vals)


    def _should_create_wallet_entry(self, vals):
        """
        Determine if a wallet entry should be created.
        """
        order_status = self.env['order.status'].browse(vals.get('order_status_id'))
        return (
            not self.wallet_move_id and self.is_wallet_reversed and
            order_status.code not in ['1', '2', '3', '5']
        )

    def _process_wallet_entry(self, vals, status):
        """
        Process wallet entry creation.
        """
        if status != 'sale':
            return

        partner = self.billing_partner_id if self.service_type_id.is_qshop_service else self.partner_id
        wallet_config = self._get_wallet_config()

        # Validate wallet balance
        total_amt = self._get_total_amount(vals)
        self._check_wallet_balance(partner, wallet_config, total_amt)

        # Create merchant entry if needed
        if self.service_type_id.is_qshop_service and vals.get('order_status_id') in [4, "4"]:
            self._create_wallet_merchant_entry(wallet_config)

        # Create account move
        self._create_account_move(wallet_config, partner, total_amt)

    def _should_create_merchant_entry(self, vals):
        """
        Determine if a merchant wallet entry should be created.
        """
        order_status = self.env['order.status'].browse(vals.get('order_status_id'))
        return (
            not self.merchant_wallet_move_id and
            self.service_type_id.is_qshop_service and
            order_status.code == "4"
        )

    def _process_merchant_entry(self, vals):
        """
        Process merchant wallet entry creation.
        """
        partner = self.billing_partner_id if self.service_type_id.is_qshop_service else self.partner_id
        wallet_config = self._get_wallet_config()

        # Validate wallet balance
        total_amt = self.merchant_order_amount if self.wallet_move_id else (self.total_amount + self.merchant_order_amount)
        self._check_wallet_balance(partner, wallet_config, total_amt)

        # Create merchant entry
        self._create_wallet_merchant_entry(wallet_config)

    def _get_wallet_config(self):
        """
        Retrieve wallet configuration, raising an error if missing.
        """
        wallet_config = self.env['customer.wallet.config'].sudo().search([], limit=1)
        if not wallet_config:
            raise exceptions.ValidationError('Journal configuration missing for customer wallet')
        return wallet_config

    def _get_total_amount(self, vals):
        """
        Compute the total amount to validate against the wallet balance.
        """
        total_amt = self.total_amount
        if self.service_type_id.is_qshop_service and vals.get('order_status_id') == "4":
            total_amt += self.merchant_order_amount
        return total_amt

    def _check_wallet_balance(self, partner, wallet_config, total_amt):
        """
        Check if the wallet has sufficient balance.
        """
        wallet_bal = self.env['res.partner'].sudo().compute_wallet_balance(
            partner, wallet_config, fields.Date.context_today(self)
        )
        if wallet_bal < total_amt:
            raise exceptions.ValidationError('Your wallet does not have enough balance.')

    def _create_account_move(self, wallet_config, partner, total_amt):
        """
        Create account move for wallet transactions.
        """
        move_vals = {
            'partner_id': partner.id,
            'journal_id': wallet_config.journal_id.id,
            'company_id': self.env.user.company_id.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'move_type': 'entry',
            'wallet_order_id': self.order_id,
            'ref': f"Delivered Order - {self.order_id}",
            'service_type_id': self.service_type_id.id,
            'date': fields.Datetime.now(self).date(),
            'wallet_transaction_ref_id': self.wallet_transaction_ref_id,
            'order_transaction_no': f"WRD_{self.wallet_transaction_ref_id}_{self.order_id}",
            'line_ids': [
                (0, 0, {
                    'partner_id': partner.id,
                    'account_id': wallet_config.default_credit_account_id.id,
                    'credit': 0.0,
                    'debit': self.total_amount,
                    'name': 'Deducted',
                    'wallet_order_id': self.order_id or False,
                }),
                (0, 0, {
                    'partner_id': partner.id,
                    'account_id': wallet_config.wallet_inter_account_id.id,
                    'credit': self.total_amount,
                    'debit': 0.0,
                    'name': 'Deducted',
                'wallet_order_id': self.order_id or False,
                }),
            ],
        }
        account_move = self.env['account.move'].sudo().create(move_vals)
        account_move.sudo().post()
        self.wallet_move_id = account_move.id
    def write(self, vals):
        if vals.get('state') or vals.get('order_status_id'):
            self.action_update_wallet_transaction(vals)

        res = super(SaleOrder, self).write(vals)
        return res
