# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
from lxml import etree



class Expense_ClaimAdvPaymentWiz(models.TransientModel):
    """
    Wizard to get and payment information and create a payment in account.payment
    """
    _name = 'expense.claim.payment.wizard'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(Expense_ClaimAdvPaymentWiz, self).get_view(view_id=view_id, view_type=view_type, **options)

        if self.env.context.get('default_payment_type') == 'inbound':
            doc = etree.XML(res['arch'])
            # Modify domain for journal_id field
            journal_id_field = doc.xpath("//field[@name='journal_id']")
            if journal_id_field:
                journal_id_field[0].set('domain',
                                        "[('type','in', ('bank','cash')),('is_cashfree', '=', False)]")

            # Modify the button's string attribute
            button_element = doc.xpath("//button[@name='action_advance_payment']")
            if button_element:
                # Set the button's string dynamically
                button_element[0].set('string', "Collect Balance")
            res['arch'] = etree.tostring(doc, encoding='unicode')

        return res

    @api.model
    def default_get(self, field_list):
        """Function to get values for payment method, cashfree journal"""
        res = super().default_get(field_list)
        payment_method_id = self.env['account.payment.method'].search(
            [('payment_type', '=', self.env.context.get('default_payment_type')),
             ('code', '=', 'manual')], limit=1)
        cashfree_journal = self.env['account.journal'].search([('is_cashfree', '=', True)], limit=1)
        active_ids = self.env.context.get('active_ids')
        claim = self.env['hr.expense.claim'].browse(active_ids)
        def_fields = {'partner_id': claim.requested_by.user_partner_id.id,
                      'payment_method_id': payment_method_id.id,
                      'comments': claim.name,
                      'journal_id': cashfree_journal.id,
                      }
        res.update(def_fields)
        return res

    partner_id = fields.Many2one('res.partner', string='Employee')
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method', required=True)
    comments = fields.Char(string='Comments')
    amount = fields.Float(string="Amount")
    date = fields.Date(string='Date', default=datetime.today())
    journal_id = fields.Many2one('account.journal', string='Journal')
    payment_through = fields.Selection([("online", "Online"), ("bank", "Bank")])

    @api.onchange('payment_through')
    def onchange_payment_through(self):
        """Function to change values based on payment through field value"""
        for rec in self:
            if rec.payment_through == 'online':
                if self.env.context.get('default_payment_type') == 'inbound':
                    raise ValidationError(_("cannot create payment through online for Balance Collection"))
                else:
                    cashfree_journal = self.env['account.journal'].search([('is_cashfree', '=', True)], limit=1)
                    if cashfree_journal:
                        rec.journal_id = cashfree_journal.id
                    else:
                        rec.journal_id = False
            elif rec.payment_through == 'bank':
                bank_journal = self.env['account.journal'].search([('is_bank_journal', '=', True)], limit=1)
                if bank_journal:
                    rec.journal_id = bank_journal.id
                else:
                    rec.journal_id = False
            else:
                rec.journal_id = False

    def action_advance_payment(self):
        """Function to create payment record in account.payment"""
        for rec in self:
            if rec.amount == 0:
                raise ValidationError(_("Not allowed to create payment with zero amount."))
            active_ids = self.env.context.get('active_ids')
            claim = self.env['hr.expense.claim'].browse(active_ids)
            values = {
                'partner_type': 'supplier',
                'partner_id': rec.partner_id.id,
                'journal_id': rec.journal_id.id,
                'amount': rec.amount,
                'date': rec.date,
                'payment_method_id': rec.payment_method_id.id,
                'ref': claim.name,
                'claim_id': claim.id,
                'state': 'draft',
                'company_id':claim.company_id.id
            }

            payment = self.env['account.payment'].create(values)
            payment.action_post()
            if payment.journal_id.is_cashfree:
                line_list = [(0, 0, {'transaction_date': fields.datetime.now(),
                                     'payment_state': 'initiate'})]
                payment.write({'is_cashfree': True})
                payment.write({'is_cashfree': True, 'cashfree_payment_line_ids': line_list})
                payment.action_cashfree_payment()
            claim.payment_ids = [(4, payment.id)]

            if self.env.context.get('expense_advance'):
                claim.write({'is_advance_payed': True, 'advance_payed_amount': rec.amount})
            elif self.env.context.get('expense_payout'):
                claim.action_reconcile_payment(payment)
            elif self.env.context.get('expense_pay_in'):
                claim.is_pay_in_done = True
                claim.action_reconcile_payment(payment)
            claim._compute_expense_approval_stage()
            form_view = self.env.ref('account.view_account_payment_form')
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'res_id': payment.id,
                'view_mode': 'form',
                'view_id': form_view.id,
                'context': {'create': False},
                'target': 'current',
            }
