from odoo import models, fields, api, _

class InvoiceExceptionlog(models.Model):
    _name = "invoice.exception.log"
    _description = "Invoice Exception Log"
    _rec_name = "invoice_id"
    _order = "id desc"

    invoice_id = fields.Many2one('account.move', string="Invoice", index=True)
    order_id = fields.Char(string='Order ID')
    access_date = fields.Datetime(string='Executed Date',
                                  default=fields.Datetime.now)
    response = fields.Text(string='Response')
    is_reexecuted_completed = fields.Boolean("Is completed")
