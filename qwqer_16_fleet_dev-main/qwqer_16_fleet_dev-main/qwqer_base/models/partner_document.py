# -*- coding: utf-8 -*-

from odoo import fields, models


class PartnerDocumentLine(models.Model):
    """
    This model contains documents of partner
    """
    _name = 'partner.document.line'
    _description = 'Partner Document'
    
    
    document_name = fields.Char(string="Document Name")
    file_name = fields.Char(string="File Name")
    file = fields.Binary(string='Attachment', attachment=True)
    partner_id = fields.Many2one('res.partner',string='Partner')
