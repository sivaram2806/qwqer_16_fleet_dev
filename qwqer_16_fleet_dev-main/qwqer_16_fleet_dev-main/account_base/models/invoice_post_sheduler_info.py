from odoo import models, fields, api
from datetime import date, timedelta, datetime


class InvoicePostSchedulerInfo(models.Model):
    _name = 'invoice.post.scheduler.info'

    scheduler_start_time = fields.Datetime("Scheduler Start Time")
    scheduler_end_time = fields.Datetime("Scheduler End Time")
    picked_records = fields.Integer("Picked Records")
    processed_records = fields.Integer("Processed Records")
    exception_count = fields.Integer("Failed Count")

    def clear_invoice_scheduler_info(self):
        flush_date = date.today() - timedelta(days=30)
        records = self.search([('create_date', '<=', flush_date.strftime('%Y-%m-%d'))])
        if records:
            records.unlink()
