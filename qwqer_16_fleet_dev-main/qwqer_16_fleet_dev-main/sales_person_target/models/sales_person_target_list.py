from datetime import datetime, timedelta
from email.policy import default

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

from odoo.tools.populate import compute


class SalesPersonTargetList(models.Model):
    _name = "salesperson.target.list"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Sales Person Monthly Target List"

    sales_person_id = fields.Many2one("hr.employee", string="Sales Person", tracking=True)
    sales_person_domain = fields.Many2many(comodel_name='hr.employee',compute='_compute_sales_person_domain',store=True)
    target_revenue = fields.Float("Target Revenue", tracking=True)
    collection_target = fields.Float("Collection Target", tracking=True)
    target_id = fields.Many2one('target.configuration', 'Target', ondelete="cascade", tracking=True)
    period = fields.Selection(string="Period", related='target_id.period', store=True)
    name = fields.Char(related='target_id.name', string='Target Name', store=True)
    state_id = fields.Many2one('res.country.state', related='target_id.state_id', store=True)
    region_domain = fields.Many2many(comodel_name='sales.region', compute='_compute_region_domain', store=True)
    region_id = fields.Many2one('sales.region', string='Region', tracking=True)
    create_date = fields.Datetime(string="Create Date", default=lambda self: fields.Datetime.now())
    achieved_revenue = fields.Float("Achieved Revenue (Trip)",
                                    compute='_compute_sales_person_wise_total_achieved_revenue', store=True)
    achieved_revenue_percentage = fields.Float("Achieved Revenue %",
                                               compute='_compute_sales_person_wise_total_achieved_revenue', store=True)
    achieved_collection = fields.Float("Achieved Collection", compute='_compute_sales_person_wise_total_achieved_revenue',
                                       store=True)
    achieved_collection_percentage = fields.Float("Achieved Collection %",
                                                  compute='_compute_sales_person_wise_total_achieved_revenue', store=True)
    from_date = fields.Date(string="From Date", related='target_id.from_date', store=True)
    to_date = fields.Date(string="To Date", related='target_id.to_date', store=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    @api.constrains('sales_person_id', 'region_id', 'period')
    def _check_sales_person_unique(self):
        for rec in self:
            if rec.target_id and rec.sales_person_id and rec.region_id and rec.period:
                target_list = self.env['salesperson.target.list'].search([
                    ('target_id', '=', rec.target_id.id), ('sales_person_id', '=', rec.sales_person_id.id),
                    ('region_id', '=', rec.region_id.id)])
                if len(target_list) > 1:
                    raise UserError(_("Salesperson cannot be assigned multiple targets for the same region and period"))

    @api.depends('state_id')
    def _compute_region_domain(self):
        for rec in self:
            if rec.state_id.regions_ids:
                rec.region_domain = rec.state_id.regions_ids.ids
            else:
                rec.region_domain = []

    @api.depends('region_id')
    def _compute_sales_person_domain(self):
        for rec in self:
            if rec.region_id:
                sales_person_ids = self.env['hr.employee'].search([
                    ('company_id', "=", rec.company_id.id),
                    ('user_id.displayed_regions_ids', 'in', rec.region_id.id)])
                if sales_person_ids:
                    rec.sales_person_domain = sales_person_ids
                else:
                    rec.sales_person_domain = []


    @api.depends('achieved_revenue', 'achieved_revenue_percentage', 'achieved_collection', 'target_revenue',
                 'achieved_collection_percentage', 'collection_target',
                 'sales_person_id', 'period', 'from_date', 'to_date', 'region_id')
    def _compute_sales_person_wise_total_achieved_revenue(self):
        ftl_achieved_revenue = 0.0
        urban_haul_achieved_revenue = 0.0
        for rec in self:
            rec.achieved_revenue = 0.0
            rec.achieved_revenue_percentage = 0.0
            rec.achieved_collection = 0.0
            rec.achieved_collection_percentage = 0.0
            if not rec.sales_person_id or not rec.from_date or not rec.to_date or not rec.region_id:
                rec.achieved_revenue = 0
                continue
            ftl_batch_trip = self.env['batch.trip.ftl'].search([('state', 'in', ['finance_approved', 'completed']),
                                                                ('sales_person_id', '=', rec.sales_person_id.id),
                                                                ('trip_date', '>=', rec.from_date),
                                                                ('trip_date', '<=', rec.to_date),
                                                                ('region_id', '=', rec.region_id.id)])
            if ftl_batch_trip:
                # Total sum of trp amount for ftl
                ftl_achieved_revenue = sum(ftl_batch_trip.mapped('total_trip_amount'))

            urban_haul_batch_trip = self.env['batch.trip.uh'].search([('state', 'in', ['approved', 'completed']),
                                                                      ('sales_person_id', '=', rec.sales_person_id.id),
                                                                      ('trip_date', '>=', rec.from_date),
                                                                      ('trip_date', '<=', rec.to_date),
                                                                      ('region_id', '=', rec.region_id.id)])
            if urban_haul_batch_trip:
                # Total Sum Calculation For Urban Haul
                urban_haul_achieved_revenue = sum(urban_haul_batch_trip.mapped('customer_total_amount'))

            rec.achieved_revenue = ftl_achieved_revenue + urban_haul_achieved_revenue
            if rec.target_revenue > 0 and rec.achieved_revenue > 0:
                rec.achieved_revenue_percentage = (rec.achieved_revenue / rec.target_revenue) * 100

            """ Calculate the Achieved collection based on the ftl and urban haul Daily trips"""

            payments = self.env['account.payment'].search([('state', '=', 'posted'),
                                                           ('payment_type', '=', 'inbound'),
                                                           ('sales_person_id', '=',rec.sales_person_id.id),
                                                           ('date', '>=', rec.from_date),
                                                           ('date', '<=', rec.to_date),
                                                           ('region_id', '=', rec.region_id.id)])
            if payments:
                rec.achieved_collection = sum(payments.mapped('amount'))
                if rec.collection_target > 0 and rec.achieved_collection > 0:
                    rec.achieved_collection_percentage = (rec.achieved_collection / rec.collection_target) * 100
