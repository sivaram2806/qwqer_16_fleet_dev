# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date
import logging
from odoo.exceptions import MissingError

_logger = logging.getLogger(__name__)


class CashFreePayin(models.Model):
    _name = 'cashfree.payin'
    _description = 'CashFree Payment Payin'
    _rec_name = 'link_id'
    _order = 'id desc'

    link_id = fields.Char(string='Link Id')
    currency_id = fields.Many2one(comodel_name='res.currency')
    amount_paid = fields.Float(string='Amount Paid')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    purpose = fields.Char(string='Purpose')
    customer_phone = fields.Char(string='Customer Phone')
    cf_link_id = fields.Char(string='CF Link ID')
    transaction_id = fields.Char(string='Transaction Id')
    event_time = fields.Char('Transaction Date')
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')])
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money'),
                                     ('transfer', 'Internal Transfer')], string='Payment Type')
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method' )
    journal_id = fields.Many2one('account.journal', string='journal')
    payment_id = fields.Many2one('account.payment', string='Payment')
    state = fields.Selection(selection=[('draft', 'Draft'), ('paid', 'Validated')],
                             readonly=True, default='draft', string="State")
    partner_id = fields.Many2one('res.partner', string='Partner', related='invoice_id.partner_id')
    # new
    payment_status = fields.Char(string='Payment Status')
    order_id_num = fields.Char(string='Order Id')
    transaction_status = fields.Char(string='Transaction Status')
    response_json = fields.Json(string='Response')

    @api.model
    def create(self, vals):

        # Update event_time and currency_id in vals
        if vals.get('response_json'):

            # Search for existing payment record
            payment_rec = self.env['cashfree.payin'].sudo().search([('transaction_id', '=', vals.get('transaction_id'))])

            # If payment record exists, return a success message
            if payment_rec:
                return {
                    'transaction_id': vals.get('transaction_id'),
                    'status_code': 200,
                    'status': "SUCCESS",
                    'msg': f"Record already exists with transaction_id: {vals.get('transaction_id')}"
                }

        # Proceed with creating the record
        res = super().create(vals)

        try:
            # Fetch the Cashfree configuration
            config = self.env['cash.free.configuration'].search([('payment_type', '=', 'inbound')], limit=1)
            response_json = vals.get('response_json', {})
            if not config:
                raise MissingError(
                    "Please setup a Cashfree Configuration to receive payment using Cashfree payment link")

            # Update payment-related fields with configuration values
            res.write({
                'payment_method_id': config.payment_method_id,
                'journal_id': config.journal_id,
                'partner_type': config.partner_type,
                'payment_type': config.payment_type,
                'currency_id': vals.get('currency_id'),
                'event_time': response_json.get('event_time'),
            })

            # If auto-validation is enabled, validate the payment
            if config.is_validated:
                res.create_validate_payment_cashfree_payin(config)

            _logger.info("Cashfree Payin API: Cashfree Payment Entry Created for payment id %s",
                         vals.get('transaction_id'))
            return res

        except Exception as e:
            # Handle any exceptions during the creation process
            err_msg = str(e)
            return {
                'transaction_id': vals.get('transaction_id'),
                'status_code': 500,
                'status': "REJECTED",
                'msg': err_msg
            }

    def create_validate_payment_cashfree_payin(self, config=None):

        config = config or self.env['cash.free.configuration'].search([('payment_type', '=', 'inbound')], limit=1)
        if not config:
            raise MissingError("Please setup a Cashfree Configuration to receive payment using Cashfree payment link")
        payment = self.env['account.payment'].create({
            'partner_type': self.partner_type,
            "partner_id": self.partner_id.id,
            'amount': self.amount_paid,
            'journal_id': self.journal_id.id,
            'payment_type': self.payment_type,
            'payment_method_id': self.payment_method_id.id,
            'date': date.today(),
            'is_cashfree_payin': True,
            'ref': self.link_id})
        self.payment_id = payment

        if len(payment.line_ids) == 2:
            # Update the first record's partner_id
            payment.line_ids[0].with_context({'skip_account_move_synchronization': True, 'payin': 'payin'}).write({'partner_id': config.partner_id.id})

            # Update the second record's Label
            payment.line_ids[1].with_context({'skip_account_move_synchronization': True, 'payin': 'payin'}).update({'name': 'Payin via Cashfree'})

        if config.is_validated:
            payment.sudo().with_context({'skip_account_move_synchronization': True, 'payin': 'payin'}).action_post()
            move_lines = payment.line_ids.filtered(lambda line: not line.reconciled)
            for line in move_lines:
                self.invoice_id.js_assign_outstanding_line(line.id)
            self.state = 'paid'
        return payment