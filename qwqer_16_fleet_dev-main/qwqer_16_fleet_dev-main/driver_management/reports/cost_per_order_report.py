# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo import tools


class CostPerOrderReport(models.Model):
    _name = "cost.perorder.analysis.report"
    _description = "Cost Per Order Analysis Report"
    _auto = False
    _rec_name = 'driver_uid'
    _order = 'from_date desc'

    create_date = fields.Datetime(string="Create Date", readonly=True)
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    payment_state = fields.Selection([
        ('initiate', 'Initiated'),
        ('pending', 'Pending'),
        ('fail', 'Failed'),
        ('success', 'Success'), ], string='Status')
    daily_payout_amount = fields.Float(string='Daily Payout (A)', digits='Product Price')
    incentive_amount = fields.Float(string='Incentive (B)', digits='Product Price')
    total = fields.Float(string='Total Payout(A+B)', digits='Product Price')
    deduction_amount = fields.Float(string='Deduction (C)', digits='Product Price')
    total_payout = fields.Float(string='Total Payout (A+B-C)', digits='Product Price')
    employee_id = fields.Many2one(comodel_name='hr.employee', string="Driver")
    region_id = fields.Many2one('sales.region')
    driver_uid = fields.Char('Driver ID')
    no_of_orders = fields.Integer("Orders")
    batch_payout_id = fields.Many2one(comodel_name='driver.batch.payout', string="Payout")
    order_cost = fields.Float(string='Avg Cost Per Order', digits='Product Price')
    order_qty = fields.Integer("Order Quantity")

    vehicle_category_id = fields.Many2one(comodel_name='driver.vehicle.category', string='Vehicle Category')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(CostPerOrderReport, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)
        if 'total:sum' and 'orders:sum' in fields:
            for line in res:
                if line.get('total') and line.get('orders') and line.get('order_qty') and line.get('order_qty') != 0:
                    line['order_cost'] = line.get('total') / line.get('order_qty')
        for line in res:
            if 'total' and 'order_qty' in fields:
                if line.get('order_qty', 0) and line.get('order_qty', 0) > 0:
                    line['order_cost'] = line.get('total') / line.get('order_qty')
        return res

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
           CREATE OR REPLACE VIEW cost_perorder_analysis_report AS  (
                SELECT
                    pl.id AS id,
                    pl.create_date AS create_date,
                    pl.employee_id AS employee_id,
                    pl.region_id AS region_id,
                    pl.driver_uid AS driver_uid,
         
                    pl.daily_payout_amount AS daily_payout_amount,
                    pl.incentive_amount AS incentive_amount,
                    pl.deduction_amount AS deduction_amount,
                    pl.total_payout AS total_payout,
                    pl.payment_state AS payment_state,
                    pl.from_date AS from_date,
                    pl.to_date AS to_date,
                    pl.batch_payout_id AS batch_payout_id,
                    SUM(dp.no_of_orders) AS no_of_orders,
                    SUM(dp.order_qty) AS order_qty,
                    COALESCE(pl.daily_payout_amount + pl.incentive_amount, pl.daily_payout_amount) AS total,
                    CASE
                        WHEN SUM(dp.order_qty) > 0 THEN COALESCE(pl.daily_payout_amount + pl.incentive_amount, pl.daily_payout_amount) / SUM(dp.order_qty)
                        ELSE 0
                    END AS order_cost
                FROM
                    driver_batch_payout_lines pl
                INNER JOIN
                    driver_batch_payout tp ON pl.batch_payout_id = tp.id
                INNER JOIN
                    hr_employee hr ON pl.employee_id = hr.id

                LEFT JOIN
                    driver_payout dp ON pl.batch_payout_id = dp.batch_payout_id AND pl.employee_id = dp.employee_id
                GROUP BY
                    pl.id,
                    pl.region_id,
                    pl.batch_payout_id,
                    pl.employee_id
                    
                );
        """)

#TODO ADD when vehicle categ added
        """
        hr.vehicle_category_id AS vehicle_category_id,
         hr.vehicle_category_id
        INNER JOIN 
            driver_vehicle_category AS vc ON hr.vehicle_category_id = vc.id"""

    # def action_get_payout_lines(self):
    #     line_ids = self.env['driver.batch.payout.lines'].search(
    #         [('payout_id', '=', self.payout_id.id), ('employee_id', '=', self.employee_id.id)])
    #     if line_ids:
    #         return {
    #             'name': _('Payout'),
    #             'view_type': 'form',
    #             'view_mode': 'tree',
    #             'res_model': 'payout.lines',
    #             'view_id': False,
    #             'type': 'ir.actions.act_window',
    #             'domain': [('id', 'in', line_ids.ids)],
    #         }
