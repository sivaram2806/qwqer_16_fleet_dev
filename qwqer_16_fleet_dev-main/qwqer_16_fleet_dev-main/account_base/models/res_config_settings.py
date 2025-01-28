# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    record_limit = fields.Integer(related="company_id.record_limit", string="Record Fetch Limit", readonly=False, store=True)
    days_limit = fields.Integer(related="company_id.days_limit", string="Days Fetch Limit", readonly=False, store=True)

    skip_start_time = fields.Selection(related="company_id.skip_start_time", string="Skip Start Hour", readonly=False, store=True)

    skip_end_time = fields.Selection(related="company_id.skip_end_time", string="Skip End Hour", readonly=False, store=True)
    post_invoice_with_cron = fields.Boolean(related="company_id.post_invoice_with_cron", string="Post Invoices",
                                            readonly=False, store=True)

    @api.constrains('skip_start_time', 'skip_end_time')
    def _validate_skip_times(self):
        if self.skip_start_time and not self.skip_end_time:
            raise UserError("Enter value for Skip End Hour")
        if not self.skip_start_time and self.skip_end_time:
            raise UserError("Enter value for Skip Start Hour")
        if int(self.skip_start_time) > 24 or int(self.skip_end_time) > 24:
            raise UserError("Enter hour in valid range max 24")
        if int(self.skip_start_time) > int(self.skip_end_time):
            raise UserError('Skip Start Hour should be lesser than Skip End Hour')
        if int(self.skip_end_time) > 0 and int(self.skip_start_time) == 0:
            raise UserError(' Enter a value more than 0 for Skip Start Hour ')
        if int(self.skip_end_time) != 0 and int(self.skip_start_time) != 0:
            if int(self.skip_end_time) == int(self.skip_start_time):
                raise UserError("Skip Start Hour and  Skip End Hour should have different values")