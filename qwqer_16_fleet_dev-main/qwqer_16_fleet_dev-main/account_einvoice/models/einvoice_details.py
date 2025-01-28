# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
import qrcode
import base64
from io import BytesIO


class EinvoiceDetails(models.Model):
    _name = 'einvoice.details'
    _rec_name = "irn"

    move_id = fields.Many2one('account.move', string="Invoice")
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

    # Company id for Multi-Company
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    @api.depends('scanned_qr_code')
    def generate_qr_code(self):
        """
        To generate QR from text
        """
        for rec in self:
            if rec.scanned_qr_code:
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10,  border=4)
                qr.add_data(rec.scanned_qr_code)
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.qr_code = qr_image

