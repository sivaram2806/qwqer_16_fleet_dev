# -*- coding: utf-8 -*-

from odoo import models, fields, exceptions, _
from datetime import timedelta, datetime
import requests
import logging
from odoo.exceptions import MissingError, UserError

_logger = logging.getLogger(__name__)


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'
    _description = 'Account Move model'

    payment_link = fields.Char(string='Payment Link', tracking=True, copy=False)
    link_expiry = fields.Char(string='Link Expiry', copy=False)
    is_paid = fields.Boolean(string="Is Paid", default=False) #V13_field: payment

    def generate_payment_link_btn(self):
        if self.payment_link:
            date_format = "%Y-%m-%dT%H:%M:%S%z"
            expiry_time = datetime.strptime(self.link_expiry, date_format)
            current_time = datetime.now(datetime.now().astimezone().tzinfo)
            if current_time > expiry_time:
                self.generate_payment_link()
            else:
                raise UserError(_("Currently available link has not expired. Please use the existing payment link \nLink: %s", self.payment_link))
        else:
            self.generate_payment_link()

    def generate_payment_link(self):
        cashfree_id = self.env['cash.free.credentials'].sudo().search([('company_id', '=', self.company_id.id)], limit=1)
        if not cashfree_id:
            raise MissingError(
                "Cashfree configuration is missing, Please contact System Administrator")
        elif not cashfree_id.name or not cashfree_id.key:
            raise MissingError(
                "Cashfree configuration is missing, Please contact System Administrator")
        url = "https://api.cashfree.com/pg/links"
        # url = "https://sandbox.cashfree.com/pg/links"
        link_expiry_time = (datetime.now() + timedelta(days=365)).isoformat() + "+05:30"
        link_concatenation_time = link_expiry_time[2:19].replace(":", "")
        invoice_name = self.name.replace("/", "-")
        link_id = invoice_name + link_concatenation_time

        payload = {
            "link_amount": str(self.amount_residual),
            "link_currency": self.currency_id.name,
            "link_purpose": "Payment For Invoice# " + str(self.name),
            "link_auto_reminders": True,
            "link_expiry_time": str((datetime.now() +
                                     timedelta(days=365)).isoformat()) + "+05:30",
            "link_id": link_id,
            "link_notes": {
                "invoice": str(self.id),
            },
            "link_notify": {
                "send_email": False,
                "send_sms": True
            },
            "customer_details": {
                "customer_name": ''.join(e for e in self.partner_id.name if e.isalnum()),
                "customer_phone": str(self.partner_id.phone)[-10:]
            },
            "link_meta": {
                "notify_url": self.env['ir.config_parameter'].sudo().get_param(
                    'web.base.url') + "/cashfree_payment/request/",
                "upi_intent": False
            },
        }
        headers = {
            "Accept": "application/json",
            "x-client-id": cashfree_id.name,
            "x-client-secret": cashfree_id.key,
            "x-api-version": "2023-08-01",
            "Content-Type": "application/json"
        }

        response = requests.request("POST", url, json=payload, headers=headers)
        if response.status_code in [200]:
            response = response.json()
            self.payment_link = response.get('link_url')
            self.link_expiry = response.get('link_expiry_time')
        else:
            response = response.json()
            _logger.info("Cashfree Payin API : {}".format(response.get('message')))
            raise MissingError(_('Cashfree Payin API : %s\n\n\nPlease verify API credentials and try again.',
                                 response.get('message')))

    # Function for canceling a generated payment link.
    def payment_abortion(self):

        # Collecting the authorization details
        cashfree_id = self.env['cash.free.credentials'].sudo().search([], limit=1)
        app_id = cashfree_id.name
        app_key = cashfree_id.key

        # Converting the link_id into needed format
        link_expiry = self.link_expiry
        link_concatenation_time = link_expiry[3:19].replace(":", "")
        link_id = self.name.replace("/", "-") + link_concatenation_time if link_expiry else self.name.replace("/", "-")

        # Generating the cancellation URL by including the link_id.
        url = f"https://api.cashfree.com/pg/links/{link_id}/cancel"
        # url = f"https://sandbox.cashfree.com/pg/links/{link_id}/cancel"

        # Setting the headers that is to be sent.
        headers = {
            "Accept": "application/json",
            "x-client-id": app_id,
            "x-client-secret": app_key,
            "x-api-version": "2023-08-01"
        }

        # Posting the request
        response = requests.post(url, headers=headers)

        # Deleting the previous payment link from form.
        self.payment_link = False

        # Function which execute payment_link_abortion on clicking reset-to-draft button.

    def button_draft(self):
        result = super().button_draft()
        # Looping is performed in consideration of multiple records scenario at selection from list view.
        for rec in self:
            # Checking whether there exists a payment link for abortion.
            if self.payment_link:
                # Checking whether the payment has been already made.
                if self.is_paid:
                    raise exceptions.Warning(_("Payment has been already made for this invoice."))
                else:
                    rec.payment_abortion()
        return result
