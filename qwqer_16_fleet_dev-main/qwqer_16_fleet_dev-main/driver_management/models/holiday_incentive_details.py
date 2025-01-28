# -*- coding:utf-8 -*-

from odoo import api, fields, models


class HolidayIncentiveDetails(models.Model):
    _name = 'holiday.incentive.details'
    _description = 'Holiday Incentive Details'
    _rec_name = 'holiday_day'
    _order = 'create_date desc'

    holiday_day = fields.Char("Day", required=1)
    holiday_date = fields.Date("Date", required=1)
    payout_plan_ids = fields.Many2many('driver.payout.plans', string="Payout Plans",required=1)
    holiday_incentive_config_ids = fields.One2many('holiday.incentive.config','holiday_id',string='Holiday Incentive Config')

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        for rec in res:
        # Loop over each payout plan selected in payout_plan_ids
            for plan in rec.payout_plan_ids:
                # Update each holiday incentive config with the current payout plan
                for holiday_incentive in rec.holiday_incentive_config_ids:
                    # Ensure the holiday incentive config is added to the holiday_incentive_ids of the payout plan
                    plan.holiday_incentive_ids = [(0, 0, {
                        'holiday_day': rec.holiday_day,
                        'holiday_date': rec.holiday_date,
                        'min_no_of_order': holiday_incentive.min_no_of_order,
                        'min_no_of_hr': holiday_incentive.min_no_of_hr,
                        'amount': holiday_incentive.amount,
                        'payout_plan_id': plan.id,
                            'plan_holiday_config_id': holiday_incentive.id,
                            'plan_holiday_details_id': rec.id
                    })]
        return res

    def write(self, vals):
        res = super(HolidayIncentiveDetails, self).write(vals)
        if 'payout_plan_ids' in vals:
            for item in vals.get("payout_plan_ids"):
                if item[0] == 6:
                    self.env["holiday.incentive.config"].search([('plan_holiday_details_id', "=", self.id), ('payout_plan_id', "not in", item[-1])]).unlink()
        if 'payout_plan_ids' in vals or 'holiday_date' in vals or 'holiday_incentive_config_ids' in vals:
            for plan in self.payout_plan_ids:
                new_incentive_ids = []
                for holiday_incentive in self.holiday_incentive_config_ids:
                    existing_record = plan.holiday_incentive_ids.filtered(
                        lambda r: r.plan_holiday_config_id.id == holiday_incentive.id
                    )
                    if existing_record:
                        existing_record.write({
                            'holiday_day': self.holiday_day,
                            'holiday_date': self.holiday_date,
                            'min_no_of_order': holiday_incentive.min_no_of_order,
                            'min_no_of_hr': holiday_incentive.min_no_of_hr,
                            'amount': holiday_incentive.amount,
                            'plan_holiday_details_id': self.id
                        })
                    else:
                        new_incentive_ids.append((0, 0, {
                            'holiday_day': self.holiday_day,
                            'holiday_date': self.holiday_date,
                            'min_no_of_order': holiday_incentive.min_no_of_order,
                            'min_no_of_hr': holiday_incentive.min_no_of_hr,
                            'amount': holiday_incentive.amount,
                            'payout_plan_id': plan.id,
                            'plan_holiday_config_id': holiday_incentive.id,
                            'plan_holiday_details_id': self.id
                        }))
                if new_incentive_ids:
                    plan.holiday_incentive_ids = new_incentive_ids

        return res

