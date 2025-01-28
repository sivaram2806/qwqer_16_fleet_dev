# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DriverPayoutPlans(models.Model):
    _name = 'driver.payout.plans'
    _description = 'Payout Plan'
    _order = 'create_date desc'
    _inherit = ['mail.thread']

    name = fields.Char("Plan", tracking=True)
    plan_seq =  fields.Char('Name', compute='compute_plan_seq', store=True)
    region_id = fields.Many2one('sales.region', string="Region", tracking=True)
    active = fields.Boolean('Active', default=True)
    emp_ids = fields.One2many('hr.employee', 'plan_detail_id', string='Driver Plans')
    is_default_region_plan = fields.Boolean(string='Default Region Plan', tracking=True)
    driver_minimum_wage_ids = fields.One2many('driver.minimum.wage.config','payout_plan_id', string='Minimum Wages')
    daily_incentive_per_order_ids = fields.One2many('daily.incentive.order.config','payout_plan_id', string='Daily Incentive Per Order')
    daily_incentive_per_hours_ids = fields.One2many('daily.incentive.hours.config','payout_plan_id', string='Daily Incentive Per Hour')
    daily_incentive_stop_count_ids = fields.One2many('daily.incentive.stop.count.config','payout_plan_id', string='Daily Incentive Per Stop Count')
    weekly_incentive_ids = fields.One2many('driver.weekly.incentive.config','payout_plan_id', string='Weekly Incentive')
    monthly_incentive_ids = fields.One2many('driver.monthly.incentive.config','payout_plan_id', string='Monthly Incentive')
    weekend_incentive_ids = fields.One2many('driver.weekend.incentive.config','payout_plan_id', string='Weekend Incentive')
    day_incentive_order_km_ids = fields.One2many('driver.incentive.day.km.config','payout_plan_id', string='Incentive Day Km')
    incentive_order_km_ids = fields.One2many('driver.incentive.order.km.config','payout_plan_id', string='Incentive Order Km')
    holiday_incentive_ids = fields.One2many('holiday.incentive.config','payout_plan_id', string='Holiday Incentive')
    driver_count = fields.Integer(string="Driver Count", compute='get_driver_count')
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    def write(self, vals):
        res = super(DriverPayoutPlans, self).write(vals)

        for rec in self:
            # Check if inactive plan has associated drivers
            if not rec.active and rec.emp_ids:
                raise UserError(
                    _("There are driver(s) attached to the plan. Please remove the driver(s) from the plan before you archive."))

            emp_list = self.env["hr.employee"].search([('active', '=', False), ('plan_detail_id', '=', rec.id)])
            if emp_list:
                raise UserError(
                    _("There are archived driver(s) attached to the plan. Please remove the driver(s) from the plan before you archive."))

            # Validate holiday dates for duplicates
            if rec.holiday_incentive_ids:
                self._check_duplicate_holidays(rec.holiday_incentive_ids)

        return res

    @api.depends('name')
    def compute_plan_seq(self):
        for rec in self:
            if not rec.name:
                continue

            company_id = self.env.company.id
            plan_seq = str(rec.plan_seq)

            # Update plan_seq if the first 3 characters are 'PLN' else generate new.
            if plan_seq.startswith('PLN'):
                rec.plan_seq = f"{plan_seq[:7]}-{rec.name}"
            else:
                seq_code = self.env['ir.sequence'].with_company(company_id).next_by_code('payout.plan.sequence')
                rec.plan_seq = f"{seq_code}-{rec.name}"

    def _check_duplicate_holidays(self, holiday_ids):
        """Checks for duplicate dates in holiday_ids and raises an error if found."""
        holiday_list = set()
        repeat_list = set()

        for line in holiday_ids:
            if line.holiday_date:
                date_str = f"{line.holiday_date.strftime('%d/%m/%Y')}_{line.min_no_of_order}_{line.min_no_of_hr}"
                if date_str not in holiday_list:
                    holiday_list.add(date_str)
                else:
                    if date_str not in repeat_list:
                        repeat_list.add(date_str)

        if repeat_list:
            holidays = ', '.join(repeat_list)
            raise UserError(_('Date(s) %s selected multiple times in holidays!') % holidays)

    def get_driver_count(self):
        for rec in self:
            rec.driver_count = self.env['hr.employee'].search_count([('plan_detail_id','=',rec.id)])

    def action_view_driver_list(self):
        for rec in self:
            return {
            'name': _('Drivers'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'hr.employee',
            'domain':[('plan_detail_id','=',rec.id)],
            'context':{'driver_employee': True,'driver_only': True}
            }

    def set_default_region_plan(self):
        default_driver_payout_plan = self.region_id.sudo().default_driver_payout_plan or None
        if not default_driver_payout_plan:
            self.region_id.sudo().default_driver_payout_plan = self.id
            self.is_default_region_plan = True
        else:
            return {
                'name': _('Confirm Change'),
                'type': 'ir.actions.act_window',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'driver.payout.plan.change.wizard',
                'view_id': self.env.ref(
                    'driver_management.driver_payout_plan_change_wizard_form').id,
                'context': {
                    'region': self.region_id.name,
                    'already_set_plan': default_driver_payout_plan.name,
                }
            }

    def remove_default_region_plan(self):
        if self.is_default_region_plan:
            self.region_id.sudo().default_driver_payout_plan = None
            self.is_default_region_plan = False