# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReportInvoiceWithPayment(models.AbstractModel):
    """added to pass virtual_bank_details to report"""
    _inherit = 'report.account.report_invoice_with_payments'
    
    
    @api.model
    def _get_report_values(self, docids, data=None):
        virtual_bank_details = self.env['res.bank'].search([('is_virtual_account','=',True)],limit=1)
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': self.env['account.move'].browse(docids),
            'report_type': data.get('report_type') if data else '',
            'virtual_bank_details':virtual_bank_details
        }
