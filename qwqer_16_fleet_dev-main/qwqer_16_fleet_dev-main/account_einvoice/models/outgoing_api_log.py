#  -*- encoding: utf-8 -*-

from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)

# TODO: Move this model from here to another base module whenever we start using the logger in other modules

class OutgoingAPIlog(models.Model):
    _name = "outgoing.api.log"
    _description = "Outgoing API Log"
    _rec_name = "access_date"
    _order = "id desc"

    name = fields.Char(string="API name")
    access_date = fields.Datetime(string='Access Date',
                                  default=fields.Datetime.now)
    response_date = fields.Datetime(string='Response Date')
    data = fields.Text(string='Data Send')
    response = fields.Text(string='Response')
    key = fields.Char(string="Key")
    status = fields.Char(string="Status")
    # Company id for Multi-Company
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
