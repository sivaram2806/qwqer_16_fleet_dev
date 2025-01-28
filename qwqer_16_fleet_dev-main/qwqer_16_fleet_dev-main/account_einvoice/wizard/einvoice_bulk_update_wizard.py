# -*- coding: utf-8 -*-
from odoo import fields, models
from datetime import timedelta

class EinvoiceBulkInvoiceWizard(models.TransientModel):
    _name = 'einvoice.bulk.invoice.wizard'
    _rec_name = "next_run_date"
    
    next_run_date = fields.Date("Next Execution Date")
    state_gst = fields.Many2one('einvoice.config','GSTIN')
    payment_mode_ids = fields.Many2many('payment.mode', string='Payment Mode',related="state_gst.payment_mode_ids")
    record_limit = fields.Integer("Record Fetch Limit",related="state_gst.record_limit")
    
    def action_einvoice_create(self):
        """
            Action to call bulk e-invoice creation based on user selection
        """
        next_run_date = (self.next_run_date + timedelta(days=1))
        self.env['account.move'].action_einvoice_bulk_create(next_run_date,self.state_gst)
        