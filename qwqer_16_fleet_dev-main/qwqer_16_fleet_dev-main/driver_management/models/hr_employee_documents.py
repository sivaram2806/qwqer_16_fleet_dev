# -*- coding:utf-8 -*-

from odoo import fields, models

class HrEmployeeDocuments(models.Model):
    """
    Model contains records from Hr Employee Documents
    """
    _name = 'hr.employee.documents'
    _description = 'Hr Employee Documents'
    _rec_name = 'doc_type_id'
    _order = 'doc_type_id asc'

    description = fields.Text("Description")
    exp_date = fields.Date(string="Expiry Date",copy=False)
    doc_type_id = fields.Many2one('driver.document.type',string="Document Name")
    document_type = fields.Selection([
    ("bank", "Bank"),
    ("kyc", "KYC"),
    ("vehicle", "Vehicle"),
    ("pan", "PAN"),
    ], string='Document Type', related='doc_type_id.type') #V13_field : name
    doc_file = fields.Binary(string="Document", attachment=True, copy=False)
    emp_id = fields.Many2one('hr.employee', string='Employee')

    #TODO @api.onchange('doc_type_id')
    # def get_doc_type(self):
    #     doc_lst=[]
    #     docs = self.env['vehicle.document.type'].search([('is_driver','=',False)])
    #     for doc in docs:
    #         doc_lst.append(doc.id)
    #     domain = {'doc_type_id': [('id', 'in', doc_lst)]}
    #     return {'domain': domain}