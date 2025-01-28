# -*- coding:utf-8 -*-

from odoo import api, fields, models

DOCUMENT_TYPE = [
    ("bank", "Bank"),
    ("kyc", "KYC"),
    ("vehicle", "Vehicle"),
    ("pan", "PAN"),
]


class DriverDocumentType(models.Model):
    _name = 'driver.document.type'
    _description = 'Document Type'

    name = fields.Char('Name',tracking=True)
    code = fields.Char('Code', tracking=True)
    type = fields.Selection(DOCUMENT_TYPE, default=DOCUMENT_TYPE[0][0], copy=False, tracking=True)