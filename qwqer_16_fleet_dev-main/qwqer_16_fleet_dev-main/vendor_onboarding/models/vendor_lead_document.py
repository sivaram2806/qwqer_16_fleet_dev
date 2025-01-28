# -*- coding: utf-8 -*-

from odoo import fields, models


class VendorLeadDocumentLine(models.Model):
    """
    This model contains documents of vendor
    """
    _name = 'vendor.lead.document.line'
    _description = 'Vendor Lead Document'

    document_name = fields.Char(string="Document Name")
    file_name = fields.Char(string="File Name")
    file = fields.Binary(string='Attachment', attachment=True)
    vendor_lead_id = fields.Many2one('vendor.lead', string='Vendor Lead')
