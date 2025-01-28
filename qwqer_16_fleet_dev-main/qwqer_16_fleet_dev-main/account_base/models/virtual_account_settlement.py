# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class VirtualAccountSettlement(models.Model):
    _name = 'virtual.account.settlement'
    _description = 'to create payments against virtual account statement  '

    name = fields.Char(string='Customer Code')
    buyer_code = fields.Char(string='Buyer Code')
    date = fields.Date(string="Date")
    utr = fields.Char(string='UTR')
    remitter_ifsccode = fields.Char(string='Remitter IFSCCODE')
    amount = fields.Float(string='Amount')
    customer_account_number = fields.Char(string='Customer Account Number')
    sender_name = fields.Char(string='Sender Name')
    payment_product_code = fields.Char(string='Payment Product Code')
    beneficiary_code = fields.Char(string='Beneficiary Bank Code')
    journal_id = fields.Many2one("account.journal", string='Journal')
    partner_id = fields.Many2one('res.partner', string='Partner')
    payment_id = fields.Many2one('account.payment', string='Payment')
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], )
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money'),
                                     ('transfer', 'Internal Transfer')], string='Payment Type',
                                    required=True)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method')
    validated = fields.Boolean(string="validated")
    button_visible = fields.Boolean(string="Button")
    state = fields.Selection(selection=[('draft', 'Draft'), ('paid', 'validated')], readonly=True, default='draft',
                             string="State")
    # Company id for Multi-Company
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    def create_validate_payment_for_virtual_statements(self):
        """
            To create payments against a statement record
        """
        for rec in self:
            if not self.validated:
                payment = self.env['account.payment'].create({
                    'partner_type': rec.partner_type,
                    'partner_id': rec.partner_id.id,
                    'amount': rec.amount,
                    'journal_id': rec.journal_id.id,
                    'payment_type': rec.payment_type,
                    'payment_method_id': rec.payment_method_id.id,
                    'date': rec.date,
                    'company_id': rec.company_id.id
                })
                payment.sudo().action_post()
                rec.state = 'paid'
                rec.payment_id = payment
                rec.validated = True

    @api.model
    def create(self, vals):
        config = self.env['virtual.account.configuration'].search([('company_id', '=', self.env.company.id)], limit=1)
        virtual_bank_account = False
        if vals.get('buyer_code') and vals.get('name'):
            virtual_bank_account = vals.get('name') + vals.get('buyer_code')
        partner = self.env['res.partner'].search([('virtual_bank_acc', '=', virtual_bank_account)])
        if partner:
            result_pool = False
            if vals.get('utr') and vals.get('date'):
                result_pool = self.env['virtual.account.settlement'].search(
                    [('utr', '=', vals.get('utr')), ('date', '=', vals.get('date'))])
            if not result_pool:
                vals.update({'partner_id': partner.id,
                             'journal_id': config.journal_id.id,
                             'partner_type': config.partner_type,
                             'payment_method_id': config.payment_method_id.id,
                             'payment_type': config.payment_type,
                             'validated': False})

                res = super(VirtualAccountSettlement, self).create(vals)
                if config.is_validated:
                    res.create_validate_payment_for_virtual_statements()
                return res
            else:
                raise UserError(_('The virtual account settlement is already created for the UTR %s in %s ') % (
                vals.get('utr'), vals.get('date')))
        else:
            raise UserError(_('The partner is not found with the virtual account number %s ') % (virtual_bank_account))

    def reset_to_draft(self):
        """reset payment if created against a virtual account entry"""
        if self.payment_id:
            self.payment_id.action_draft()
            self.payment_id.action_cancel()
            self.state = 'draft'
            self.payment_id = False
            self.validated = False
