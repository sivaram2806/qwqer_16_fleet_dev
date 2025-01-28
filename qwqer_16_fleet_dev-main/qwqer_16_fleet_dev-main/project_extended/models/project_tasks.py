import json
import logging
import pytz
import datetime
import requests

from odoo import api, fields, models, _
from lxml import etree
from odoo.exceptions import UserError, ValidationError, Warning, AccessError
from datetime import datetime, timedelta, date
from odoo.tools import format_datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

class Project(models.Model):
    _inherit = "project.project"

    project_code = fields.Integer('Project Code')

class ProjectTask(models.Model):
    _inherit = "project.task"
    _order = "create_date desc"

    @api.model
    def create(self, vals):
        new_name = self.env['ir.sequence'].next_by_code('project.task')
        vals.update({'ticket_no': new_name})
        res = super(ProjectTask, self).create(vals)
        return res

    def _group_gro_user_domain(self):
        """We are taking the users with gro groups for giving domain for gros field"""
        group = self.env.ref('project_extended.group_gro_user', raise_if_not_found=False)
        return [('groups_id', 'in', group.ids)] if group else []

    reference_no = fields.Char('Reference No', tracking=True)
    ticket_no = fields.Char(string='Ticket No', tracking=True)
    region_id = fields.Many2one('sales.region', string='Region', tracking=True)
    state_id = fields.Many2one('res.country.state', string='State', tracking=True)
    source_id = fields.Many2one('sys.source', tracking=True)
    category_id = fields.Many2one('sys.category', tracking=True)
    order_no = fields.Char(string="Order ID", tracking=True)
    customer_name = fields.Char(string="Customer Name", tracking=True)
    customer_phone = fields.Char(string="Customer Phone No", tracking=True)
    cause_id = fields.Many2one('cause.config.settings', string='Cause', tracking=True)
    sub_category = fields.Many2one('ondc.subcategory.config.settings', string='Sub Category', tracking=True)
    ondc_order_no = fields.Char('ONDC Order ID', tracking=True)
    buyer_action = fields.Selection([('processing', 'PROCESSING'), ('open', 'OPEN'), ('closed', 'CLOSED')], 'Action',
                                    tracking=True)
    buyer_short_description = fields.Char(string='Short Description', tracking=True)
    buyer_write_time = fields.Datetime(string='Updated At', tracking=True)
    buyer_organisation_name = fields.Char(string='Buyer Organisation Name', tracking=True)
    buyer_phone = fields.Char(string='Phone', tracking=True)
    buyer_email = fields.Char(string='Email', tracking=True)
    buyer_name = fields.Char(string='Person Name', tracking=True)
    seller_action = fields.Selection([('cascaded', 'CASCADED'), ('processing', 'PROCESSING')], 'Action', tracking=True)
    seller_short_description = fields.Char(string='Short Description', tracking=True)
    seller_write_time = fields.Datetime(string='Updated at', tracking=True)
    seller_organisation_name = fields.Char(string='Seller Organisation Name', tracking=True)
    seller_phone = fields.Char(string='Phone', tracking=True)
    seller_email = fields.Char(string='Email', tracking=True)
    seller_name = fields.Char(string='Person Name', tracking=True)
    transaction_id = fields.Char(string='Transaction ID', tracking=True)
    bap_uri = fields.Text(string='Bap URI', tracking=True)
    expected_response_time = fields.Char(string='Expected Response Time', tracking=True)
    expected_resolution_time = fields.Char(string='Expected Resolution Time', tracking=True)
    issue_state = fields.Selection([('open', 'OPEN'), ('closed', 'CLOSED')], string='State', default='open',
                                   readonly=True, tracking=True)
    image_ids = fields.Many2many('ir.attachment', string='Attachments')
    state_action = fields.Selection([('cancel', 'CANCEL'), ('no_action', 'NO ACTION'), ('refund', 'REFUND')],
                                    default='no_action', tracking=True)
    is_action_visible = fields.Boolean('Is Action Visible')
    is_resolved = fields.Boolean('Is Resolved', default=False, store=True)
    resolution_short_desc = fields.Char('Short Desc', tracking=True)
    resolution_long_desc = fields.Char('Long Desc', tracking=True)
    gro_type = fields.Char('GRO Type')
    gros = fields.Many2many('res.users', string='GROs', domain=_group_gro_user_domain)

    @api.onchange('project_id')
    def get_customer(self):
        for data in self:
            if data.project_id:
                data.customer_name = data.project_id.partner_id.name

    @api.onchange('region_id')
    def get_state(self):
        for data in self:
            if data.region_id:
                data.state_id = data.region_id.state_id