# -*- coding: utf-8 -*-
from odoo import models, api, _, fields
from odoo.exceptions import UserError
import qrcode
import base64
from io import BytesIO
import json
import time
from datetime import datetime, timedelta, time
import logging

_logger = logging.getLogger(__name__)
import pytz


class AccountMove(models.Model):
    _inherit = 'account.move'

    irn = fields.Text(string="IRN", copy=False)
    ack_no = fields.Char("Ack No", copy=False)
    ack_date = fields.Datetime("Ack Date", copy=False)
    scanned_qr_code = fields.Text("Scanned QR Code", copy=False)

    einvoice_generated = fields.Boolean(string="E-Invoice Generated", copy=False)
    qr_code = fields.Binary("QR Code", compute='generate_qr_code', attachment=True, store=True, copy=False)
    cancel_reason_code = fields.Selection([("1", 'Duplicate Invoice'), ("2", 'Data Entry Mistake')], string="Reason",
                                          copy=False)
    cancel_reason_remark = fields.Text("Remark", copy=False)
    is_einv_scheduler_executed = fields.Boolean(string="Is E-Invoice Scheduler Executed?", copy=False)
    einvocie_details_ids = fields.One2many('einvoice.details', 'move_id', string='Einvoice Details', copy=False)

    @api.depends('scanned_qr_code')
    def generate_qr_code(self):
        """QR code text to Binary converter"""
        for rec in self:
            if rec.scanned_qr_code:
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, ox_size=10, border=4)
                qr.add_data(rec.scanned_qr_code)
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.qr_code = qr_image

    def get_utc_datetime(self, date):
        """To get UTC time from user/context time zone"""
        if date:
            tz_name = self.env.user.tz or self._context.get('tz') or 'UTC'
            local = pytz.timezone(tz_name)
            local_dt = local.localize(fields.Datetime.from_string(date), is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            return fields.Datetime.to_string(utc_dt)

    def action_einvoice_create(self, einvoice_config=None, force_authenticate=False):
        """
        To Generate E-invoice for invoices by authentication TAXPRO and
        """
        for rec in self:
            if rec.irn:
                raise UserError("Irn already Generated")

            if not rec.partner_id.vat:
                raise UserError(_("GSTIN not available for the customer."))
            if not einvoice_config:
                einvoice_config = self.env['einvoice.config'].search([
                    ('api_gstin', '=', rec.journal_gstin_partner_id.vat)], limit=1)
            einvoice_config.authenticate_tax_pro(force_authenticate=force_authenticate)

            if einvoice_config.auth_token:
                url = einvoice_config.generate_url_with_auth_data()
            else:
                raise UserError(_("E-Invoice authentication failed"))
            print("calling fetch_irn_from_gst_portal ================================== ")
            response_content, outgoing_request_log = einvoice_config.fetch_irn_from_gst_portal(url, rec)
            print("response_content ------------------------------------------ ", response_content)
            rec.update_einvoice_details_and_status(response_content, einvoice_config, outgoing_request_log)

    def update_einvoice_details_and_status(self, response_content, einvoice_config, outgoing_request_log,
                                           scheduler=False):
        """

        @param response_content:
        @param einvoice_config:
        @param scheduler:
        """

        status = response_content.get('Status')
        status_cd = response_content.get("status_cd")
        if status in [0, '0', 1, '1']:
            status = str(status)
        if status_cd in [0, '0', 1, '1']:
            status_cd = str(status_cd)
        outgoing_request_log.sudo().update({
            'response': response_content,
            'response_date': datetime.now(),
            'status': "Success" if status == "1" or status_cd == "1" else "Failed"
        })
        if status == '1' or status_cd == '1':
            response_data = json.loads(response_content['Data'])
            ack_date = self.get_utc_datetime(response_data['AckDt'])

            self.env['einvoice.details'].sudo().create({
                "ack_no": response_data['AckNo'],
                "ack_date": ack_date,
                "irn": response_data['Irn'],
                "scanned_qr_code": response_data['SignedQRCode'],
                "einvoice_generated": True,
                "move_id": self.id
            })
            self.einvoice_generated = True
            self.ack_date = ack_date
            if scheduler:
                self.is_einv_scheduler_executed = True
        elif status == '0':
            if response_content['ErrorDetails'][0]['ErrorCode'] in ['2150']:
                info_dtls = response_content['InfoDtls'][0]['Desc']
                ack_date = self.get_utc_datetime(info_dtls['AckDt'])
                self.env['einvoice.details'].sudo().create({
                    "ack_no": info_dtls['AckNo'],
                    "ack_date": ack_date,
                    "irn": info_dtls['Irn'],
                    "einvoice_generated": True,
                    "move_id": self.id
                })
                self.einvoice_generated = True
                self.ack_date = ack_date
            elif response_content['ErrorDetails'][0]['ErrorCode'] in ['GSP752']:
                self.action_einvoice_create(einvoice_config=einvoice_config, force_authenticate=True)

            if scheduler:
                self.env['einvoice.scheduler.failed.log'].sudo().create({
                    'invoice_id': self.id,
                    'gstin': einvoice_config.api_gstin,
                    'reason': "\n".join(
                        [item.get('ErrorMessage', "") for item in response_content.get('ErrorDetails', []) if
                         item.get('ErrorMessage', "")])
                })
                self.is_einv_scheduler_executed =  True
            else:
                self.env.cr.commit()
                raise UserError("\n".join(
                    [item.get('ErrorMessage', "") for item in response_content.get('ErrorDetails', []) if
                     item.get('ErrorMessage', "")]))
        elif status_cd == '0':
            if response_content.get('error', {}).get('error_cd', '') == '2150':
                info_dtls = response_content['InfoDtls'][0]['Desc']
                ack_date = self.get_utc_datetime(info_dtls['AckDt'])
                self.env['einvoice.details'].sudo().create({
                    "ack_no": info_dtls['AckNo'],
                    "ack_date": ack_date,
                    "irn": info_dtls['Irn'],
                    "einvoice_generated": True,
                    "move_id": self.id
                })
                self.einvoice_generated = True
                self.ack_date = ack_date
            else:
                self.env['einvoice.scheduler.failed.log'].sudo().create({
                    'invoice_id': self.id,
                    'gstin': einvoice_config.api_gstin,
                    'reason': response_content.get('error', {}).get('message')
                })
                error = response_content.get('error')
                if error:
                    if error.get('error_cd') == "GSP752":
                        self.action_einvoice_create(einvoice_config=einvoice_config, force_authenticate=True)

            self.is_einv_scheduler_executed = True

    def button_draft(self):
        if self.move_type == "out_refund":
            if self.reversed_entry_id:
                raise UserError(_("You are not allowed to move the credit note to draft which is mapped to invoice."))

        account_moves = self.env['account.move'].search(
            [('reversed_entry_id', '!=', False), ('reversed_entry_id', '=', self.id), ('state', '!=', 'cancel')])
        if account_moves:
            raise UserError(_("You are not allowed to move the invoice to draft once the credit note is created"))
        if self.einvoice_generated:
            current_datetime = fields.datetime.now()
            irn_cancel_datetime = self.ack_date and self.ack_date + timedelta(days=1) or False
            if irn_cancel_datetime and irn_cancel_datetime < current_datetime:
                raise UserError(
                    _("IRN is already generated for the invoice. You are not allowed to cancel the invoice"))
        res = super().button_draft()
        return res

    def button_cancel(self):
        for moves in self:
            if moves.einvoice_generated:
                if 'from_api' in self._context and self._context.get('from_api', False):
                    raise UserError(
                        _("sale order and the invoice cancellation restricted, as einvoice is already generated."))
        return super(AccountMove, self).button_cancel()

    def action_reverse(self):
        account_moves = self.env['account.move'].search(
            [('reversed_entry_id', '=', self.id), ('state', '!=', 'cancel')])
        if account_moves:
            raise UserError(_("Credit note already exist for the invoice."))

        action = super(AccountMove, self).action_reverse()

        return action

    def action_post(self):
        """
        In posting a move checking whether irn is generated or not, and restricting if generated
        """
        if self.einvoice_generated:
            raise UserError(
                _("IRN is already generated for the invoice. You are not allowed to post the invoice again."))
        return super().action_post()

    def _compute_edit_access(self):
        super(AccountMove)._compute_edit_access()
        for rec in self:
            if not rec.edit_remove:
                if rec.einvoice_generated and rec.state != 'posted':
                    rec.edit_remove = '<style>.o_form_button_edit {display: none !important;}</style>'
                else:
                    rec.edit_remove = False

    def einvoice_bulk_create_scheduler(self):
        """
        Scheduler for creating e-invoices for non-credit payment modes
        """
        next_run_date = fields.datetime.now()
        einvoice_config = self.env['einvoice.config'].search(
            [('next_run_date', '=', next_run_date), ('is_scheduler_run', '=', True)], limit=1)

        exec_start_time = time(int(einvoice_config.exec_start_time), 0)
        exec_end_time = time(int(einvoice_config.exec_end_time), 0)

        user_id = self.env.user
        local = pytz.timezone(user_id.tz or pytz.utc)
        convert_time = (datetime.now(local).time()).strftime('%H:%M:%S')
        check_time = datetime.strptime(str(convert_time), '%H:%M:%S').time()
        if exec_start_time <= check_time <= exec_end_time:
            self.action_einvoice_bulk_create(next_run_date.date(), einvoice_config)
        else:
            pass

    def action_einvoice_bulk_create(self, next_run_date, scheduler_config):
        """
        To create e-invoices for multiple invoices from scheduler or bulk e-invoice wizard
        @param next_run_date:
        @param scheduler_config:
        """
        if scheduler_config:
            scheduler_config.authenticate_tax_pro(scheduler=True)
            yesterday = (next_run_date + timedelta(days=-1)).strftime("%Y-%m-%d 00:00:00")
            tomorrow = next_run_date + timedelta(days=1)

            invoice_list = self.env['account.move'].search([
                ('is_einv_scheduler_executed', '=', False), ('einvoice_generated', '=', False),
                ('partner_id.vat', '!=', False), ('journal_gstin_partner_id.vat', '=', scheduler_config.api_gstin),
                ('date', '=', yesterday), ('state', '=', 'posted'),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('payment_mode_id', 'in', scheduler_config.payment_mode_ids.ids)],
                limit=scheduler_config.record_limit)
            if not invoice_list:
                scheduler_config.next_run_date = tomorrow
            else:
                for inv in invoice_list:
                    url = False
                    if scheduler_config.auth_token:
                        url = scheduler_config.generate_url_with_auth_data()
                    else:
                        self.env['einvoice.scheduler.failed.log'].sudo().create({
                            'invoice_id': inv.id,
                            'gstin': scheduler_config.api_gstin,
                            'reason': "E-Invoice authentication failed"
                        })
                    response_content, outgoing_request_log = scheduler_config.fetch_irn_from_gst_portal(url, inv)
                    print("irn response_content ===================================== ", response_content)
                    inv.update_einvoice_details_and_status(response_content, scheduler_config, outgoing_request_log,
                                                           scheduler=True)
