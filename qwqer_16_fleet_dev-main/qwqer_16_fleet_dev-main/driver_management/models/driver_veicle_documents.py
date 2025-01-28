# -*- coding:utf-8 -*-

from odoo import fields, models

class DriverVehicleDocuments(models.Model):
    """
    Model contains records from Driver Vehicle Documents, #V13_model name: vehicle.documents
    """
    _name = 'driver.vehicle.documents'
    _description = 'Driver Vehicle Documents'
    _rec_name = 'doc_type_id'
    _order = 'doc_type_id asc'


    doc_type_id = fields.Many2one('driver.document.type',string="Document Name")
    document_type = fields.Selection([
    ("bank", "Bank"),
    ("kyc", "KYC"),
    ("vehicle", "Vehicle"),
    ("pan", "PAN"),
    ], string='Document Type', related='doc_type_id.type')
    document_number = fields.Char(string="Document No")
    exp_date = fields.Date('Exp Date')
    doc_file = fields.Char(string = "Document link")
    docs = fields.Binary(string="Attachment", attachment=True, copy=False)
    emp_id = fields.Many2one('hr.employee', string='Employee')