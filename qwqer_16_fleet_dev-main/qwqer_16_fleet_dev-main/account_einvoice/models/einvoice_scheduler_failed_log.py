#  -*- encoding: utf-8 -*-


from odoo import models, fields


class EinvoiceCancelReason(models.Model):
    _name = 'einvoice.scheduler.failed.log'

    invoice_id = fields.Many2one('account.move',string="Invoice")
    reason = fields.Text("Failed Reason")
    gstin = fields.Char("GSTIN")

    # Company id for Multi-Company
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)