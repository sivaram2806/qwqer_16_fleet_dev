from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError,Warning


class PayoutPlanConfigChecker:
    """This is a wrapper class for check payout plan line config"""

    def config_val_check(self, rec, config, config_fields):
        for res in rec:
            model_fields_vals = {field: res[field] for field in config_fields if field in res._fields}
            if all(model_fields_vals.get(model_field) == 0 or False for model_field in config_fields):
                raise ValidationError(_(f'Please Enter a Proper Configuration, All fields of {config} cannot be 0'))
            if any(model_fields_vals.get(model_field) < 0 for model_field in config_fields):
                raise ValidationError(
                    _(f'Please Enter a Proper Configuration, {config} fields cannot be less than 0'))


class DriverMinimumWageConfig(models.Model):

    _name = 'driver.minimum.wage.config'
    _description = 'Driver Minimum Wage Per Day'
    _order = 'min_hrs,min_orders'

    min_hrs = fields.Float("Min no of Hours")
    min_orders = fields.Integer("Min no of Orders")
    min_amount = fields.Float("Amount (Rs)")
    payout_plan_id = fields.Many2one('driver.payout.plans',string="Payout Plan")

    def create(self, vals):
        res = super(DriverMinimumWageConfig, self).create(vals)
        model_fields = ['min_hrs', 'min_orders', 'min_amount']
        PayoutPlanConfigChecker().config_val_check(res, ' Minimum Wages config', model_fields)
        return res

    def write(self, vals):
        res = super(DriverMinimumWageConfig, self).write(vals)
        model_fields = ['min_hrs', 'min_orders', 'min_amount']
        PayoutPlanConfigChecker().config_val_check(self, ' Minimum Wages config', model_fields)
        return res


class DailyIncentiveOrderConfig(models.Model):

    _name = 'daily.incentive.order.config'
    _description = 'Daily Incentive Order Configuration'
    _order = 'min_orders'

    min_orders = fields.Integer("From (no of orders)")
    max_orders = fields.Integer("To (no of orders)")
    amount_per_order = fields.Float("Amount (Rs per order)")
    payout_plan_id = fields.Many2one('driver.payout.plans',string="Payout Plan")

    @api.constrains('min_orders', 'max_orders')
    def _check_min_max_orders(self):
        for rec in self:
            # Fetch all records with the same plan_id excluding the current record
            plans = self.search([
                ('payout_plan_id', '=', rec.payout_plan_id.id),
                ('id', '!=', rec.id)
            ])
            if rec.min_orders and rec.max_orders:
                for plan in plans:
                    # Check for overlap in ranges
                    if (plan.min_orders <= rec.min_orders <= plan.max_orders) or (plan.min_orders <= rec.max_orders <= plan.max_orders):
                        raise ValidationError(
                            _('In Daily Incentive(Orders) Range ({}, {}) Overlap With ({}, {})').format(
                                rec.min_orders, rec.max_orders, plan.min_orders, plan.max_orders
                            ))

    def create(self, vals):
        res = super(DailyIncentiveOrderConfig, self).create(vals)
        model_fields = ['min_orders', 'max_orders', 'amount_per_order']
        PayoutPlanConfigChecker().config_val_check(res, 'Daily Incentive Order config', model_fields)
        return res

    def write(self, vals):
        res = super(DailyIncentiveOrderConfig, self).write(vals)
        model_fields = ['min_orders', 'max_orders', 'amount_per_order']
        PayoutPlanConfigChecker().config_val_check(self, 'Daily Incentive Order config', model_fields)
        return res


class DailyIncentiveHoursConfig(models.Model):

    _name = 'daily.incentive.hours.config'
    _description = 'Daily Incentive Hours Configuration'
    _order = 'min_hours'

    min_hours = fields.Float("From(hrs)")
    max_hours = fields.Float("To(hrs)")
    amount_per_hour = fields.Float(" Amount (Rs per hr)")
    payout_plan_id = fields.Many2one('driver.payout.plans',string="Payout Plan")

    @api.constrains('min_hours', 'max_hours')
    def _check_min_max_hours(self):
        for rec in self:
            # Fetch all records with the same plan_id excluding the current record
            plans = self.search([
                ('payout_plan_id', '=', rec.payout_plan_id.id),
                ('id', '!=', rec.id)
            ])
            if rec.min_hours and rec.max_hours:
                for plan in plans:
                    # Check for overlap in ranges
                    if (plan.min_hours <= rec.min_hours < plan.max_hours) or (
                            plan.min_hours < rec.max_hours <= plan.max_hours):
                        raise ValidationError(
                            _('In Daily Incentive(Hours) Range ({}, {}) Overlap With ({}, {})').format(
                                rec.min_hours, rec.max_hours, plan.min_hours, plan.max_hours
                            ))

    def create(self, vals):
        res = super(DailyIncentiveHoursConfig, self).create(vals)
        model_fields = ['min_hours', 'max_hours', 'amount_per_hour']
        PayoutPlanConfigChecker().config_val_check(res, 'Daily Incentive Hours config', model_fields)
        return res

    def write(self, vals):
        res = super(DailyIncentiveHoursConfig, self).write(vals)
        model_fields = ['min_hours', 'max_hours', 'amount_per_hour']
        PayoutPlanConfigChecker().config_val_check(self, 'Daily Incentive Hours config', model_fields)
        return res

class DailyIncentiveStopCount(models.Model):

    _name = 'daily.incentive.stop.count.config'
    _description = 'Daily Incentive Stop Count Configuration'
    _order = 'start_count'

    start_count = fields.Integer("Start(Stop Count)")
    end_count = fields.Integer("End(Stop Count)")
    amount_per_stop_count = fields.Float(" Amount (Rs per Stop Count)")
    payout_plan_id = fields.Many2one('driver.payout.plans',string="Plan")

    @api.constrains('start_count', 'end_count')
    def _check_min_max_stop_count(self):
        for rec in self:
            # Fetch all records with the same plan_id excluding the current record
            plans = self.search([
                ('payout_plan_id', '=', rec.payout_plan_id.id),
                ('id', '!=', rec.id)
            ])
            if rec.start_count and rec.end_count:
                for plan in plans:
                    # Check for overlap in ranges
                    if (plan.start_count <= rec.start_count < plan.end_count) or (
                            plan.start_count < rec.end_count <= plan.end_count):
                        raise ValidationError(
                            _('In Daily Incentive (Stop Count) Range ({}, {}) Overlap With ({}, {})').format(
                                rec.start_count, rec.end_count, plan.start_count, plan.end_count
                            ))

    def create(self, vals):
        res = super(DailyIncentiveStopCount, self).create(vals)
        model_fields = ['start_count', 'start_count', 'amount_per_stop_count']
        PayoutPlanConfigChecker().config_val_check(res, 'Daily Incentive Stop config', model_fields)
        return res

    def write(self, vals):
        res = super(DailyIncentiveStopCount, self).write(vals)
        model_fields = ['start_count', 'start_count', 'amount_per_stop_count']
        PayoutPlanConfigChecker().config_val_check(self, 'Daily Incentive Stop config', model_fields)
        return res

class DriverWeeklyIncentiveConfig(models.Model):
    _name = 'driver.weekly.incentive.config'
    _description = 'Driver Weekly Incentive Configuration'
    _order = 'no_of_days,min_hours,min_orders'

    no_of_days = fields.Integer("No of Days")
    min_hours = fields.Float("Min no of Hours")
    min_orders = fields.Integer("Min no of Orders")
    amount = fields.Float(" Amount")
    payout_plan_id = fields.Many2one('driver.payout.plans',string="Plan")

    @api.constrains('no_of_days','min_hours','min_orders')
    def _check_min_values(self):
        plan_ids = self.search([('payout_plan_id', '=', self.payout_plan_id.id)])
        for rec in self:
            same_no_of_day_line = plan_ids.filtered(lambda x: x.no_of_days == rec.no_of_days and
                                                              x.min_hours == rec.min_hours and
                                                              x.min_orders == rec.min_orders and x.id != rec.id)
            if same_no_of_day_line:
                raise ValidationError(_('Same Incentive combination is already added in weekly incentive'))
            no_value_line = plan_ids.filtered(lambda x: x.no_of_days == 0 and
                                                              x.min_hours == 0 and
                                                              x.min_orders == 0 and x.amount == 0 and x.id != rec.id)
            if no_value_line:
                raise ValidationError(_('Please select a value greater than 0 for Weekly incentive.'))

    def create(self, vals):
        res = super(DriverWeeklyIncentiveConfig, self).create(vals)
        model_fields = ['no_of_days', 'min_hours', 'min_orders','amount']
        PayoutPlanConfigChecker().config_val_check(res, 'Weekly Incentive config', model_fields)
        return res

    def write(self, vals):
        res = super(DriverWeeklyIncentiveConfig, self).write(vals)
        model_fields = ['no_of_days', 'min_hours', 'min_orders','amount']
        PayoutPlanConfigChecker().config_val_check(self, 'Weekly Incentive config', model_fields)
        return res

class DriverMonthlyIncentiveConfig(models.Model):
    _name = 'driver.monthly.incentive.config'
    _description = 'Driver Monthly Incentive Configuration'
    _order = 'no_of_days,min_hours,min_orders'

    no_of_days = fields.Integer("No of Days")
    min_hours = fields.Float("Min no of Hours")
    min_orders = fields.Integer("Min no of Orders")
    amount = fields.Float(" Amount")
    payout_plan_id = fields.Many2one('driver.payout.plans',string="Plan")

    def create(self, vals):
        res = super(DriverMonthlyIncentiveConfig, self).create(vals)
        model_fields = ['no_of_days', 'min_hours', 'min_orders','amount']
        PayoutPlanConfigChecker().config_val_check(res, 'Monthly Incentive config', model_fields)
        return res

    def write(self, vals):
        res = super(DriverMonthlyIncentiveConfig, self).write(vals)
        model_fields = ['no_of_days', 'min_hours', 'min_orders','amount']
        PayoutPlanConfigChecker().config_val_check(self, 'Monthly Incentive config', model_fields)
        return res


class DriverWeekendIncentiveConfig(models.Model):

    _name = 'driver.weekend.incentive.config'
    _description = 'Driver Weekend Incentive Configuration'
    _order = 'week_days'

    week_days = fields.Selection([('sun','Sunday'),('mon','Monday'),('tue','Tuesday'),('wed','Wednesday'),('thu','Thursday'),('fri','Friday'),('sat','Saturday')],string="Day of Week")
    min_orders = fields.Integer("Min no of Orders")
    min_hours = fields.Float("Min no of Hours")
    amount = fields.Float("Amount")
    payout_plan_id = fields.Many2one('driver.payout.plans',string="Plan")

    @api.constrains('week_days')
    def _check_week_days(self):
        plan_ids = self.search([('payout_plan_id','=',self.payout_plan_id.id)])
        for rec in self:
            if rec.week_days and plan_ids:
                same_day_line = plan_ids.filtered(lambda x: x.week_days == rec.week_days and x.id != rec.id)
                if same_day_line:
                    raise ValidationError(_('%s is already added in weekend incentive'%(dict(rec._fields['week_days'].selection).get(rec.week_days))))

    def create(self, vals):
        res = super(DriverWeekendIncentiveConfig, self).create(vals)
        model_fields = ['min_orders', 'min_hours', 'amount']
        PayoutPlanConfigChecker().config_val_check(res, 'Weekend Incentive config', model_fields)
        return res

    def write(self, vals):
        res = super(DriverWeekendIncentiveConfig, self).write(vals)
        model_fields = ['min_orders', 'min_hours', 'amount']
        PayoutPlanConfigChecker().config_val_check(self, 'Weekend Incentive config', model_fields)
        return res

class DriverIncentiveDayKMConfig(models.Model):
    _name = 'driver.incentive.day.km.config'
    _description = 'Driver Incentive Day KM Configuration'
    _order = 'start_km,end_km'

    start_km = fields.Float("From(KM)")
    end_km = fields.Float("To(KM)")
    amount = fields.Float(" Amount")
    payout_plan_id = fields.Many2one('driver.payout.plans',string="Plan")

    @api.constrains('start_km', 'end_km')
    def _check_min_max_distance(self):
        for rec in self:
            # Fetch all records with the same plan_id excluding the current record
            plans = self.search([
                ('payout_plan_id', '=', rec.payout_plan_id.id),
                ('id', '!=', rec.id)
            ])
            if rec.start_km and rec.end_km:
                for plan in plans:
                    # Check for overlap in ranges
                    if (plan.start_km <= rec.start_km < plan.end_km) or (
                            plan.start_km < rec.end_km <= plan.end_km):
                        raise ValidationError(
                            _('In Incentive Day KM(Punch-In to Punch-Out) Range ({}, {}) Overlap With ({}, {})').format(
                                rec.start_km, rec.end_km, plan.start_km, plan.end_km
                            ))

    def create(self, vals):
        res = super(DriverIncentiveDayKMConfig, self).create(vals)
        model_fields = ['start_km', 'end_km', 'amount']
        PayoutPlanConfigChecker().config_val_check(res, 'Incentive Day KM config', model_fields)
        return res

    def write(self, vals):
        res = super(DriverIncentiveDayKMConfig, self).write(vals)
        model_fields = ['start_km', 'end_km', 'amount']
        PayoutPlanConfigChecker().config_val_check(self, 'Incentive Day KM config', model_fields)
        return res


class DriverIncentiveOrderKMConfig(models.Model):
    _name = 'driver.incentive.order.km.config'
    _description = 'Driver Incentive Order KM Configuration'
    _order = 'start_km,end_km'

    start_km = fields.Float("From(KM)")
    end_km = fields.Float("To(KM)")
    amount = fields.Float(" Amount")
    payout_plan_id = fields.Many2one('driver.payout.plans',string="Plan")

    @api.constrains('start_km', 'end_km')
    def _check_min_max_distance(self):
        for rec in self:
            # Fetch all records with the same plan_id excluding the current record
            plans = self.search([
                ('payout_plan_id', '=', rec.payout_plan_id.id),
                ('id', '!=', rec.id)
            ])
            if rec.start_km and rec.end_km:
                for plan in plans:
                    # Check for overlap in ranges
                    if (plan.start_km <= rec.start_km < plan.end_km) or (
                            plan.start_km < rec.end_km <= plan.end_km):
                        raise ValidationError(
                            _('In Incentive Order KM(Pickup to Drop) Range ({}, {}) Overlap With ({}, {})').format(
                                rec.start_km, rec.end_km, plan.start_km, plan.end_km
                            ))

    def create(self, vals):
        res = super(DriverIncentiveOrderKMConfig, self).create(vals)
        model_fields = ['start_km', 'end_km', 'amount']
        PayoutPlanConfigChecker().config_val_check(res, 'Incentive Order KM config', model_fields)
        return res

    def write(self, vals):
        res = super(DriverIncentiveOrderKMConfig, self).write(vals)
        model_fields = ['start_km', 'end_km', 'amount']
        PayoutPlanConfigChecker().config_val_check(self, 'Incentive Order KM config', model_fields)
        return res

class HolidayIncentiveConfig(models.Model):

    _name = 'holiday.incentive.config'
    _description = 'Holiday Incentive Config'

    holiday_day = fields.Char('Day')
    holiday_date = fields.Date("Date")
    min_no_of_order = fields.Integer("Min no of Orders")
    min_no_of_hr = fields.Float("Min no of Hours")
    amount = fields.Float("Amount")
    holiday_id = fields.Many2one('holiday.incentive.details',string="Day")
    payout_plan_id = fields.Many2one('driver.payout.plans',string="Plan")
    plan_holiday_config_id = fields.Many2one('holiday.incentive.config',string="Plan",
                                             help="Added to identify Related config id in config screen", ondelete="cascade")
    plan_holiday_details_id = fields.Many2one('holiday.incentive.details',string="Day",
                                              help="Added to identify Related config id in config screen",)

    def create(self, vals):
        res = super(HolidayIncentiveConfig, self).create(vals)
        model_fields = ['min_no_of_order', "min_no_of_hr", "amount"]
        PayoutPlanConfigChecker().config_val_check(res, 'Holiday Incentive config', model_fields)
        return res

    def write(self, vals):
        res = super(HolidayIncentiveConfig, self).write(vals)
        model_fields = ['min_no_of_order', "min_no_of_hr", "amount"]
        PayoutPlanConfigChecker().config_val_check(self, 'Holiday Incentive config', model_fields)
        return res
