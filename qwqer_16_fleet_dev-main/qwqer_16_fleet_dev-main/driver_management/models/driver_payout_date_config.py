from odoo import api, fields, models


class DriverPayoutDateConfig(models.Model):
    _name = 'driver.payout.date.config'
    _description = 'Driver Payout Last Update Date'

    daily_trans_date = fields.Date("Attendance Daily Transaction Date")
    so_daily_trans_date = fields.Date("Sales Order Daily Transaction Date")
    monthly_trans_date = fields.Date("Monthly Transaction Date")
    weekly_trans_date = fields.Date("Weekly Transaction Date")
    payout_status_date = fields.Date(string="Payout Status Update Date")
    pending_payout_sts_date = fields.Date(string="Pending Payout Status Update Date") #V13_field : pending_payout_status_dt
    pending_payout_limit = fields.Integer(string="Pending Payout Limit")
    so_daily_trans = fields.Boolean(string="Sales Order Daily Transaction Failed")
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
