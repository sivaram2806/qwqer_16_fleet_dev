# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning, ValidationError
import datetime


class PaymentRequest(models.Model):
    _name = 'payment.request'
    _inherit = ['mail.thread']
    _description = 'Payment Request'
    _mail_post_access = 'read'
    _order = 'id desc'

    @api.model
    def message_new(self, msg, custom_values=None):
        """ Create new payment request upon receiving new email"""
        defaults = {
            'subject': msg.get('subject') or _("No Subject"),
            'body': msg.get('body'),
            'name': msg.get('subject') or _("No Subject"),
            'date': msg.get('date'),
            'email': '',
            'cc_email': msg.get('cc'),
            'partner_id': False
        }
        # Extract the name from the from email if you can
        if "<" in msg.get('from') and ">" in msg.get('from'):
            start = msg.get('from').rindex("<") + 1
            end = msg.get('from').rindex(">", start)
            from_email = msg.get('from')[start:end]
        else:
            from_email = msg.get('from')
        defaults['email'] = from_email
        # Try to find the partner using the from email
        search_partner = self.env['res.partner'].sudo().search([('email', '=', from_email)], limit=1)
        if search_partner:
            defaults['partner_id'] = search_partner.id
        return super(PaymentRequest, self).message_new(msg, custom_values=defaults)

    def _notify_get_groups(self):
        """ Give access button to users and portal customer as portal is integrated
        in sale. Customer and portal group have probably no right to see
        the document so they don't have the access button. """
        groups = super(PaymentRequest, self)._notify_get_groups()
        self.ensure_one()
        for group_name, group_method, group_data in groups:
            group_data['has_button_access'] = False
        return groups

    def message_update(self, msg, update_vals=None):
        """ Override to function to create payment request for all replay mails. """
        # msg.update({'references': '', 'in_reply_to': ''})
        self.message_new(msg, custom_values=None)
        return super(PaymentRequest, self).message_update(msg, update_vals=update_vals)

    name = fields.Char(string="Name", copy=False)
    date = fields.Datetime(string="Date", copy=False)
    subject = fields.Char(string="Subject", copy=False)
    email = fields.Char(string="From", copy=False)
    cc_email = fields.Char(string="Emails CC", copy=False)
    body = fields.Text(string="Body", copy=False)
    bill_id = fields.Many2one('account.move', string='Bill')
    partner_id = fields.Many2one('res.partner', string='Vendor',
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    payment_req = fields.Boolean(string='Payment Request')
    state = fields.Selection([('draft', 'Draft'),
                              ('payment_request', 'Payment Request'),
                              ('vendorbill_prepared', 'Vendor Bill Prepared'),
                              ('vendorbill_posted', 'Vendor Bill Posted'),
                              ('payment_processed', 'Payment Processed'),
                              ('ignore', 'Ignored'),
                              ('cancelled', 'Cancelled')], default='draft', copy=False, track_visibility='onchange',
                             string="Status")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    def mark_create_payment(self):
        for rec in self:
            sequence_code = 'payment.req.sequence'
            rec.name = self.env['ir.sequence'].next_by_code(sequence_code) or '/'
            rec.state = 'payment_request'
            rec.payment_req = True

    def ignore_payment_req_mail(self):
        for rec in self:
            if rec.state == 'draft':
                rec.state = 'ignore'
            else:
                raise Warning(_("Please Make Sure All Selected Mails are in Draft State"))

    def action_darft(self):
        for rec in self:
            if rec.state in ('ignore', 'payment_request'):
                rec.state = 'draft'
                rec.name = '/'
                rec.payment_req = False
            else:
                raise Warning(_("Please Make Sure All Selected Mails are in Ignored or Payment Request State"))

    def action_sent_mail(self):
        for rec in self:
            self.ensure_one()
            ir_model_data = self.env['ir.model.data']

            try:

                template_id = ir_model_data._xmlid_lookup('payment_request.payment_req_replay_mail')[2]

            except ValueError:

                template_id = False

            try:

                compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]

            except ValueError:

                compose_form_id = False

            ctx = {

                'default_model': 'payment.request',

                'default_res_id': self.id,

                'default_use_template': bool(template_id),

                'default_template_id': template_id,

                'default_composition_mode': 'comment',

                'mark_so_as_sent': True,

                'force_email': True,

                'time':str(datetime.datetime.now().strftime(('%d-%m-%Y')))

            }

            return {

                'type': 'ir.actions.act_window',

                'view_mode': 'form',

                'res_model': 'mail.compose.message',

                'views': [(compose_form_id, 'form')],

                'views_id': compose_form_id,

                'target': 'new',

                'context': ctx,


            }

    def create_bill(self):
        if self.partner_id:
            journal = self.env['account.journal'].search([('type', '=', 'purchase'),('company_id','=',self.company_id.id)], limit=1)
            invoice = self.env['account.move']
            self.bill_id = invoice.create({
                'move_type': 'in_invoice',
                'invoice_date': fields.Date.today(),
                'date': fields.Date.today(),
                'partner_id': self.partner_id.id,
                'payment_req_id': self.id,
                'journal_id': journal and journal.id or False
            })
            attachment_ids = self.env['ir.attachment'].sudo().search(
                [('res_model', '=', 'payment.request'), ('res_id', '=', self.id)])
            if self.bill_id and attachment_ids:
                for attachment in attachment_ids:
                    if attachment.type == 'binary' and attachment.datas:
                        self.env['ir.attachment'].sudo().create({
                            'type': 'binary',
                            'res_model': 'account.move',
                            'res_id': self.bill_id.id,
                            'datas': attachment.datas,
                            'name': attachment.name,
                            'mimetype': attachment.mimetype,
                        })
        #                 self.bill_id.message_post(attachment_ids=self.message_main_attachment_id.ids)
        else:
            raise UserError(_("Please Choose Vendor for the payment request %s") % self.name)

    def create_vendor_bill(self):
        for rec in self:
            rec.state = 'vendorbill_prepared'
            rec.payment_req = True
            rec.create_bill()

    def update_status(self):
        for rec in self:
            if rec.bill_id and rec.bill_id.payment_state == "paid" and rec.bill_id.state == "posted":
                rec.state = "payment_processed"


