# -*- coding: utf-8 -*-
import logging
from collections import defaultdict
from datetime import datetime, time, timedelta
from odoo.exceptions import AccessError

import pytz

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import formatLang, float_compare, get_lang, format_date
from odoo.tools.sql import create_index

_logger = logging.getLogger(__name__)


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'
    _description = 'Inherited for modification'
    def init(self):
        """-- Journal ID Index --
        """
        create_index(self._cr, 'account_move_name_journal_id_type_index', 'account_move', ["name", "journal_id", 'move_type'])
        super().init()

    def _post(self, soft=True):
        """Post/Validate the documents.

        Posting the documents will give it a number, and check that the document is
        complete (some fields might not be required if not posted but are required
        otherwise).
        If the journal is locked with a hash table, it will be impossible to change
        some fields afterwards.

        :param soft (bool): if True, future documents are not immediately posted,
            but are set to be auto posted automatically at the set accounting date.
            Nothing will be performed on those documents before the accounting date.
        :return Model<account.move>: the documents that have been posted
        """
        if not self.env.su and not (self.env.user.has_group('account.group_account_invoice') or self.env.user.has_group(
                'account_base.account_read_receivables_accounting_group')):
            raise AccessError(_("You don't have the access rights to post an invoice."))

        for invoice in self.filtered(lambda move: move.is_invoice(include_receipts=True)):
            if (
                invoice.quick_edit_mode
                and invoice.quick_edit_total_amount
                and invoice.currency_id.compare_amounts(invoice.quick_edit_total_amount, invoice.amount_total) != 0
            ):
                raise UserError(_(
                    "The current total is %s but the expected total is %s. In order to post the invoice/bill, "
                    "you can adjust its lines or the expected Total (tax inc.).",
                    formatLang(self.env, invoice.amount_total, currency_obj=invoice.currency_id),
                    formatLang(self.env, invoice.quick_edit_total_amount, currency_obj=invoice.currency_id),
                ))
            if invoice.partner_bank_id and not invoice.partner_bank_id.active:
                raise UserError(_(
                    "The recipient bank account linked to this invoice is archived.\n"
                    "So you cannot confirm the invoice."
                ))
            if float_compare(invoice.amount_total, 0.0, precision_rounding=invoice.currency_id.rounding) < 0:
                raise UserError(_(
                    "You cannot validate an invoice with a negative total amount. "
                    "You should create a credit note instead. "
                    "Use the action menu to transform it into a credit note or refund."
                ))

            if not invoice.partner_id:
                if invoice.is_sale_document():
                    raise UserError(_("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
                elif invoice.is_purchase_document():
                    raise UserError(_("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

            # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
            # lines are recomputed accordingly.
            if not invoice.invoice_date:
                if invoice.is_sale_document(include_receipts=True):
                    invoice.invoice_date = fields.Date.context_today(self)
                elif invoice.is_purchase_document(include_receipts=True):
                    raise UserError(_("The Bill/Refund date is required to validate this document."))

        for move in self:
            if move.state == 'posted':
                raise UserError(_('The entry %s (id %s) is already posted.') % (move.name, move.id))
            if not move.line_ids.filtered(lambda line: line.display_type not in ('line_section', 'line_note')):
                raise UserError(_('You need to add a line before posting.'))
            if not soft and move.auto_post != 'no' and move.date > fields.Date.context_today(self):
                date_msg = move.date.strftime(get_lang(self.env).date_format)
                raise UserError(_("This move is configured to be auto-posted on %s", date_msg))
            if not move.journal_id.active:
                raise UserError(_(
                    "You cannot post an entry in an archived journal (%(journal)s)",
                    journal=move.journal_id.display_name,
                ))
            if move.display_inactive_currency_warning:
                raise UserError(_(
                    "You cannot validate a document with an inactive currency: %s",
                    move.currency_id.name
                ))

            if move.line_ids.account_id.filtered(lambda account: account.deprecated):
                raise UserError(_("A line of this move is using a deprecated account, you cannot post it."))

        if soft:
            future_moves = self.filtered(lambda move: move.date > fields.Date.context_today(self))
            for move in future_moves:
                if move.auto_post == 'no':
                    move.auto_post = 'at_date'
                msg = _('This move will be posted at the accounting date: %(date)s', date=format_date(self.env, move.date))
                move.message_post(body=msg)
            to_post = self - future_moves
        else:
            to_post = self

        for move in to_post:
            affects_tax_report = move._affect_tax_report()
            lock_dates = move._get_violated_lock_dates(move.date, affects_tax_report)
            if lock_dates:
                move.date = move._get_accounting_date(move.invoice_date or move.date, affects_tax_report)

        # Create the analytic lines in batch is faster as it leads to less cache invalidation.
        to_post.line_ids._create_analytic_lines()

        # Trigger copying for recurring invoices
        to_post.filtered(lambda m: m.auto_post not in ('no', 'at_date'))._copy_recurring_entries()

        for invoice in to_post:
            # Fix inconsistencies that may occure if the OCR has been editing the invoice at the same time of a user. We force the
            # partner on the lines to be the same as the one on the move, because that's the only one the user can see/edit.
            wrong_lines = invoice.is_invoice() and invoice.line_ids.filtered(lambda aml:
                aml.partner_id != invoice.commercial_partner_id
                and aml.display_type not in ('line_note', 'line_section')
            )
            if wrong_lines:
                wrong_lines.write({'partner_id': invoice.commercial_partner_id.id})

        to_post.write({
            'state': 'posted',
            'posted_before': True,
        })

        for invoice in to_post:
            invoice.message_subscribe([
                p.id
                for p in [invoice.partner_id]
                if p not in invoice.sudo().message_partner_ids
            ])

            if (
                invoice.is_sale_document()
                and invoice.journal_id.sale_activity_type_id
                and (invoice.journal_id.sale_activity_user_id or invoice.invoice_user_id).id not in (self.env.ref('base.user_root').id, False)
            ):
                invoice.activity_schedule(
                    date_deadline=min((date for date in invoice.line_ids.mapped('date_maturity') if date), default=invoice.date),
                    activity_type_id=invoice.journal_id.sale_activity_type_id.id,
                    summary=invoice.journal_id.sale_activity_note,
                    user_id=invoice.journal_id.sale_activity_user_id.id or invoice.invoice_user_id.id,
                )

        customer_count, supplier_count = defaultdict(int), defaultdict(int)
        for invoice in to_post:
            if invoice.is_sale_document():
                customer_count[invoice.partner_id] += 1
            elif invoice.is_purchase_document():
                supplier_count[invoice.partner_id] += 1
            elif invoice.move_type == 'entry':
                sale_amls = invoice.line_ids.filtered(lambda line: line.partner_id and line.account_id.account_type == 'asset_receivable')
                for partner in sale_amls.mapped('partner_id'):
                    customer_count[partner] += 1
                purchase_amls = invoice.line_ids.filtered(lambda line: line.partner_id and line.account_id.account_type == 'liability_payable')
                for partner in purchase_amls.mapped('partner_id'):
                    supplier_count[partner] += 1
        for partner, count in customer_count.items():
            (partner | partner.commercial_partner_id)._increase_rank('customer_rank', count)
        for partner, count in supplier_count.items():
            (partner | partner.commercial_partner_id)._increase_rank('supplier_rank', count)

        # Trigger action for paid invoices if amount is zero
        to_post.filtered(
            lambda m: m.is_invoice(include_receipts=True) and m.currency_id.is_zero(m.amount_total)
        )._invoice_paid_hook()

        return to_post

    @api.depends('company_id', 'invoice_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        """To list all journals in journal entry screen"""
        for m in self:
            journal_type = m.invoice_filter_type_domain or []
            company_id = m.company_id.id or self.env.company.id
            domain = [('company_id', '=', company_id),
                      ('type', '=', journal_type)] if journal_type else [('company_id', '=', company_id)]
            m.suitable_journal_ids = self.env['account.journal'].search(domain)

    @api.onchange('invoice_line_ids')
    def on_change_invoice_line_tax(self):
        if self.invoice_line_ids.tax_ids and self.move_type == 'in_invoice' and self.partner_id.tds_threshold_check:
            tds_tax_ids = self.invoice_line_ids.tax_ids.filtered(lambda rec: rec.is_tds)._origin
            for tax in tds_tax_ids:
                amount_untaxed = self.tax_totals['amount_untaxed']
                applicable = self.check_turnover(self.partner_id.id, tax.payment_excess, amount_untaxed)
                if not applicable:
                    raise UserError(_("Vendor threshold not exceeded, so don't want to add TDS tax."))

    payment_mode_id = fields.Many2one("payment.mode",copy=False)
    is_inv_api_entry = fields.Boolean("Is Invoice API Entry")

    def check_turnover(self, partner_id, threshold, total_gross):
        domain = [('partner_id', '=', partner_id), ('account_id.account_type', '=', 'payable'),
                  ('move_id.state', '=', 'posted'), ('account_id.reconcile', '=', True)]
        journal_items = self.env['account.move.line'].search(domain)
        credits = sum([item.credit for item in journal_items])
        credits += total_gross
        if credits >= threshold:
            return True
        else:
            return False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            payment_mode_id = vals.get('payment_mode_id')
            if not payment_mode_id and self.env.context.get('default_move_type') !='in_invoice':
                vals['payment_mode_id'] = self.env.ref('account_base.payment_mode_credit').id
        return super().create(vals_list)


    def mark_invoice_to_paid_status(self):
        for invoice in self:
            if invoice.state == 'posted' and invoice.invoice_payment_state == 'not_paid':
                try:
                    payment = self.api_invoice_payment_create(invoice)
                    if payment:
                        move_line_ids = self.env['account.move.line'].sudo().search([('payment_id', '=', payment.id)])
                        for line in move_line_ids:
                            line.sudo().write({'name': 'Delivery Charges'})
                except Exception as e:
                    print("exception while invoice move to paid -------------")

    def api_invoice_payment_create(self, invoice):
        payment = False
        if invoice.payment_mode_id.code == '2':
            payment = self.env['account.payment'].with_context(active_model='account.move', active_ids=invoice.ids).create({
                'partner_type': 'customer',
                'partner_id': invoice.partner_id.id,
                'amount': invoice.amount_total,
                'journal_id': invoice.payment_mode_id.journal_id.id,
                'payment_type': 'inbound',
                'payment_method_id': 1,
                'ref': invoice.order_id or invoice.name
            })
            payment.sudo().with_context({'mode': 'online',
                                         "skip_account_move_synchronization": True}).action_post()
        elif invoice.payment_mode_id.code == '3' or invoice.payment_mode_id.code == '1':
            payment = self.env['account.payment'].with_context(active_model='account.move', active_ids=invoice.ids).create({
                'partner_type': 'customer',
                'partner_id': invoice.partner_id.id,
                'amount': invoice.amount_total,
                'journal_id': invoice.driver_id.journal_id.id,
                'payment_type': 'inbound',
                'payment_method_id': 1,
                'ref': invoice.order_id or invoice.name,
                })
            payment.sudo().with_context({'driver': invoice.driver_id.id,
                                         "skip_account_move_synchronization": True}).action_post()
        return payment

    def sale_api_invoice_post(self):
        """Scheduler to post invoices and create payments if configured."""
        scheduler_start_time = datetime.now()

        # Configuration values
        days_limit = self.env.company.days_limit
        records_limit = self.env.company.record_limit
        skip_start_time = time(int(self.env.company.skip_start_time), 0)
        skip_end_time = time(int(self.env.company.skip_end_time), 0)
        is_post = self.env.company.post_invoice_with_cron

        # Check current time against skip time range
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        current_time = datetime.now(user_tz).time()
        if skip_start_time <= current_time <= skip_end_time:
            _logger.info("Current time is within skip time range. Scheduler skipped.")
            return

        _logger.info("Starting invoice post scheduler.")

        # Fetch invoices to process
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        check_date = today - timedelta(days=days_limit)
        move_list = self.env['account.move'].search(
            [
                ('date', '>=', check_date),
                ('is_inv_api_entry', '=', True),
                ('payment_state', '=', "not_paid"),
                ('state', '=', 'draft'),
            ],
            limit=records_limit,
            order='id',
        )

        _logger.info("Invoices to process: %s", len(move_list))
        _logger.info("Is invoice posting enabled: %s", is_post)

        # Create scheduler info record
        scheduler_info = self.env['invoice.post.scheduler.info'].sudo().create({
            "scheduler_start_time": scheduler_start_time,
            "picked_records": len(move_list),
            "processed_records": 0,
            "exception_count": 0,
            "scheduler_end_time": False,
        })

        processed_records_count = 0
        exception_count = 0
        # Process invoices
        for invoice in move_list:
            if is_post:
                try:
                    with self.env.cr.savepoint():
                        invoice.sudo().action_post()
                        payment = self.api_invoice_payment_create(invoice)
                        if payment:
                            invoice_lines = invoice.line_ids.filtered(
                                lambda line: line.account_id.reconcile and not line.reconciled)
                            # Locate the payment move line (receivable/payable)
                            payment_lines = payment.line_ids.filtered(
                                lambda line: line.account_id == invoice_lines.account_id and not line.reconciled)

                            # Perform reconciliation
                            (invoice_lines + payment_lines).reconcile()
                        log_list = self.env['invoice.exception.log'].search([('invoice_id', '=', invoice.id)])
                        if log_list:
                            log_list.is_reexecuted_completed = True

                        _logger.info("Invoice %s posted successfully. Order ID: %s", invoice.id, invoice.order_id)
                        processed_records_count += 1
                except Exception as e:
                    exception_count += 1
                    self.env['invoice.exception.log'].create({
                        'invoice_id': invoice.id,
                        'order_id': invoice.order_id,
                        'response': str(e),
                    })
                    _logger.error("Invoice posting failed for %s. Error: %s", invoice.id, e)

        # Update scheduler info with results
        scheduler_info.update({
            "scheduler_end_time": datetime.now(),
            "processed_records": processed_records_count,
            "exception_count": exception_count,
        })

        _logger.info("Scheduler completed. Processed: %s, Exceptions: %s", processed_records_count, exception_count)

    def get_payment_method(self):
        for rec in self:
            flag = 0
            if rec.payment_mode_id:
                if rec.payment_mode_id.code != '5':
                    flag = 0
                else:
                    flag = 1
            else:
                if rec.order_line_ids:
                    for line in rec.order_line_ids:
                        if line.payment_mode_id.code != '5':
                            flag = 0
                            break
                        else:
                            flag += 1

            if flag > 0:
                return True
