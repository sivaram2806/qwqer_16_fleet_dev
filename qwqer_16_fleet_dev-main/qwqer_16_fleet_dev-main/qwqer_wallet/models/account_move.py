# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    order_transaction_no = fields.Char(string='Wallet Order Transaction No', index=True)
    wallet_transaction_ref_id = fields.Char(string='Wallet Cashfree ID', index=True)
    wallet_order_id = fields.Char(string='Wallet Order ID', index=True)
    comments = fields.Text("Remarks")
    is_wallet_merchant_journal = fields.Boolean("Is wallet merchant journal")
    is_wallet_active = fields.Boolean("Is Wallet Active",related='partner_id.is_wallet_active')
    customer_current_balance = fields.Float(string='Current Balance',related='partner_id.wallet_balance')


    @api.constrains('order_transaction_no')
    def _check_order_transaction_no_unique(self):
        for record in self:
            # Check if any record exists with the same order_transaction_no
            if record.order_transaction_no and self.search_count(
                    [('order_transaction_no', '=', record.order_transaction_no), ('id', '!=', record.id),('state','!=','cancel')]) > 0:
                raise ValidationError(
                    'The Order ID and its Transaction reference number must be unique!'
                )

    def check_data_invoice_post(self, account_move, move_line):
        move_line = super(AccountMove, self).check_data_invoice_post(account_move, move_line)
        if 'mode' in self._context.keys() and self._context['mode'] == 'wallet':
            wallet_config = self.env['customer.wallet.config'].search([], limit=1)
            if wallet_config:
                move_line.update({"account_id": wallet_config.wallet_inter_account_id.id})
        return move_line


    def api_invoice_payment_create(self, invoice):
        payment = super(AccountMove, self).api_invoice_payment_create(invoice)

        payment_modes = self.env['payment.mode'].search([
            ('is_wallet_payment', '=', True)
        ])

        if invoice.amount_total_signed > 0 and invoice.payment_mode_id.code in payment_modes.mapped('code'):
            payment_vals = {
                'partner_type': 'customer',
                'partner_id': invoice.partner_id.id,
                'amount': invoice.amount_total,
                'journal_id': invoice.payment_mode_id.journal_id.id,
                'payment_type': 'inbound',
                'payment_method_id': 1,
                'ref': invoice.order_id or invoice.name,
            }

            payment = self.env['account.payment'].sudo().create(payment_vals)
            payment.with_context(mode='wallet', skip_account_move_synchronization=True).action_post()
            invoice_lines = invoice.line_ids.filtered(
                lambda line: line.account_id.reconcile and not line.reconciled)
            # Locate the payment move line (receivable/payable)
            payment_lines = payment.line_ids.filtered(
                lambda line: line.account_id == invoice_lines.account_id and not line.reconciled)

            # Perform reconciliation
            (invoice_lines + payment_lines).reconcile()
            wallet_sale_order = self.env['sale.order'].search([('order_id', '=', invoice.order_id)], limit=1)
            wallet_config = self.env['customer.wallet.config'].search([('company_id','=',self.env.company.id)], limit=1)

            if wallet_config:
                wallet_move_lines = wallet_sale_order.sudo().wallet_move_id.line_ids.filtered(
                    lambda r: r.account_id == wallet_config.wallet_inter_account_id \
                              and r.wallet_order_id == invoice.order_id
                )

                payment_move_lines = payment.line_ids.filtered(
                    lambda r: r.account_id == wallet_config.wallet_inter_account_id
                )

                move_line_list = wallet_move_lines.ids + payment_move_lines.ids

                if move_line_list:
                    move_lines = self.env['account.move.line'].browse(move_line_list)
                    move_lines.reconcile(
                        # writeoff_acc_id=wallet_config.wallet_round_off_account_id,
                        # writeoff_journal_id=wallet_config.journal_id
                    )

        return payment

    def reverse_shop_wallet_entry(self, transaction_ref_id):
        wallet_config = self.env['customer.wallet.config'].search([('company_id','=',self.env.company.id)], limit=1)
        if not wallet_config:
            raise ValueError("Wallet configuration not found")

        lines = self.mapped('line_ids').filtered(
            lambda r: r.wallet_order_id == self.wallet_order_id and \
                      r.account_id == wallet_config.wallet_inter_account_id
        )

        if lines and lines.full_reconcile_id:
            # Handle reconciliation
            reconciled_round_off_lines = self.env['account.move.line'].search([
                ('full_reconcile_id', '=', lines.full_reconcile_id.id),
                ('move_id', '!=', self.id),
                ('parent_state', '=', 'posted')
            ])

            reconciled_line = reconciled_round_off_lines.move_id.line_ids.filtered(
                lambda r: r.account_id == wallet_config.wallet_round_off_account_id
            )

            lines.remove_move_reconcile()

            if reconciled_line:
                reconciled_move = reconciled_line.move_id
                reconciled_move.button_draft()
                reconciled_move.button_cancel()

        # Create reverse entry
        order_transaction_no = _('MWRE_%s_%s') % (transaction_ref_id, self.wallet_order_id)
        ref = _('Refunded Order - %s') % self.wallet_order_id

        vals = {
            'partner_id': self.partner_id.id or False,
            'date': fields.Date.today(),
            'wallet_transaction_ref_id': self.wallet_transaction_ref_id or False,
            'order_transaction_no': order_transaction_no,
            'journal_id': wallet_config.journal_id.id or False,
            'company_id': self.env.user.company_id.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'move_type': "entry",
            'service_type_id': self.service_type_id.id,
            'ref': ref,
            'line_ids': [
                (0, 0, {
                    'partner_id': self.partner_id.id,
                    'account_id': wallet_config.default_credit_account_id.id,
                    'credit': lines.credit,
                    'debit': 0.0,
                    'journal_id': wallet_config.journal_id.id,
                    'name': 'Refunded',
                    'wallet_order_id': self.wallet_order_id
                }),
                (0, 0, {
                    'partner_id': self.partner_id.id,
                    'account_id': wallet_config.wallet_inter_account_id.id,
                    'credit': 0.0,
                    'debit': lines.credit,
                    'journal_id': wallet_config.journal_id.id,
                    'name': 'Refunded',
                    'wallet_order_id': self.wallet_order_id
                })
            ]
        }

        account_move = self.env['account.move'].sudo().create(vals)
        account_move.sudo().post()

        # Reconcile move lines
        move_lines = self.env['account.move.line'].search([
            ('id', 'in', lines.filtered(lambda r: r.account_id == wallet_config.wallet_inter_account_id).ids +
             account_move.line_ids.filtered(lambda r: r.account_id == wallet_config.wallet_inter_account_id).ids)
        ])

        if move_lines:
            move_lines.reconcile()

        return account_move

    def reverse_shop_merchant_wallet_entry(self, transaction_ref_id):
        """
        Reverses the merchant wallet entry for the given transaction reference ID.

        Args:
            transaction_ref_id (str): The transaction reference ID.

        Returns:
            account.move: The newly created reversed moves, if any.
        """
        default_values_list = []
        new_moves = self.env['account.move']  # Initialize an empty recordset for new moves

        wallet_config = self.env['customer.wallet.config'].search([('company_id','=',self.env.company.id)], limit=1)
        if not wallet_config:
            return new_moves

        refund_method = "cancel"
        today = fields.Date.today()

        # Prepare default values for reversal
        for move in self:
            ref = _('Refunded merchant order - %s') % move.wallet_order_id
            order_transaction_no = _('MQMWRE_%s') % transaction_ref_id
            default_values = {
                'ref': ref,
                'date': today,
                'journal_id': move.journal_id.id,
                'invoice_payment_term_id': None,
                'wallet_order_id': move.wallet_order_id,
                'service_type_id': move.service_type_id.id,
                'order_transaction_no': order_transaction_no
            }
            default_values_list.append(default_values)

        # Organize moves into batches based on reversal method
        cancel_batch = [self.env['account.move'], []]  # Moves to be cancelled
        modify_batch = [self.env['account.move'], []]  # Other moves

        for move, default_vals in zip(self, default_values_list):
            is_cancel_needed =  refund_method in ('cancel', 'modify')
            if is_cancel_needed:
                cancel_batch[0] |= move
                cancel_batch[1].append(default_vals)
            else:
                modify_batch[0] |= move
                modify_batch[1].append(default_vals)

        # Reverse moves for each batch
        for moves, default_values, is_cancel_needed in [(cancel_batch[0], cancel_batch[1], True),
                                                        (modify_batch[0], modify_batch[1], False)]:
            if moves:
                batch_moves = moves.sudo()._reverse_moves(default_values, cancel=is_cancel_needed)
                batch_moves.line_ids.write({'name': "Merchant Amount Refunded"})
                new_moves |= batch_moves

        # Update records and return new moves
        # self.write({'merchant_wallet_move_id': False})
        return new_moves


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    wallet_order_id = fields.Char(string='Wallet Order ID')


class PaymentMode(models.Model):
    _inherit = 'payment.mode'

    is_wallet_payment = fields.Boolean("Is a Wallet Payment Mode")