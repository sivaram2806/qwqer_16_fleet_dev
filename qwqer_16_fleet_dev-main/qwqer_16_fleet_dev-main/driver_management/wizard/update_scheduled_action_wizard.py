from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

class UpdateScheduledActionWiz(models.TransientModel):
    _name = "update.scheduled.action.wiz"
    _description = "Wizard to update Scheduled Action"

    region_id = fields.Many2one(comodel_name='sales.region')
    date = fields.Date("Date")
    days = fields.Integer("Days")
    so_daily_trans = fields.Boolean("Sale Daily Trans")
    payout_type = fields.Selection(selection=[
        ('week', 'Weekly'),
        ('month', 'Monthly'),
    ], string='Payout Type')
    action_type = fields.Selection(selection=[
        ('daily', 'Daily'),
        ('week_month', 'Weekly/Monthly'),
    ], string='Action')

    def update_so_daily_transaction_manually(self):
        """Method used to call So daily driver Transaction"""
        companies = self.env['res.company'].search([])
        for company in companies:
            last_date = self.date
            payout_config_id = self.env['driver.payout.date.config'].sudo().search([('company_id','=',company.id)], limit=1)
            obj = self.env['driver.payout']
            if last_date and payout_config_id:
                obj.driver_so_daily_transaction(payout_config_id, last_date)

    def action_attendance_transaction_daily(self):
        """Method used to call Driver total pay"""
        companies = self.env['res.company'].search([])
        for company in companies:
            last_date = self.date
            payout_config_id = self.env['driver.payout.date.config'].sudo().search([('company_id','=',company.id)], limit=1)
            obj = self.env['driver.payout']
            if last_date and payout_config_id:
                obj.driver_total_pay(payout_config_id, last_date)

    def action_submit_week_month(self):
        driver_batch_payout = self.env['driver.batch.payout']
        driver_batch_payout.compute_payout(payout_type=self.payout_type, data=None, trans_date_field=self.date)
