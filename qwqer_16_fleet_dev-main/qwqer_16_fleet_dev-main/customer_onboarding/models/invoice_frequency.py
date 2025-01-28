# -*- coding: utf-8 -*-

from odoo import api, fields, models   
    
class InvoiceFrequency(models.Model):
    _name = "invoice.frequency"
    _description = "Invoice Frequency"
    
    
    name = fields.Char("Name")
    days = fields.Integer("No of days")
    
    
   
