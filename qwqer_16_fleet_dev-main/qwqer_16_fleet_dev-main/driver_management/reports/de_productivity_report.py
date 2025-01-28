# -*- coding:utf-8 -*-

from odoo import fields, models, tools, api


class DeProductivityReport(models.Model):
    _name = "de.productivity.report"
    _description = "DE Productivity Report"
    _auto = False

    state_id = fields.Many2one('res.country.state', 'State')
    region_id = fields.Many2one('sales.region', 'Region')
    vehicle_category_id = fields.Many2one('driver.vehicle.category', string='Vehicle Category')
    manager_id = fields.Many2one('hr.employee', 'Manager')
    job_id = fields.Many2one('hr.job', 'Job Position')
    productivity_date = fields.Date('Date')
    order_count = fields.Float("Order Count")
    productivity = fields.Float("Productivity")
    driver_count = fields.Float("Driver Count")

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(DeProductivityReport, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)
        if 'order_count:sum' and 'driver_count:sum' in fields:
            for line in res:
                if line.get('order_count') and line.get('driver_count') and line.get('driver_count') != 0:
                    line['productivity'] = line.get('order_count') / line.get('driver_count')
        return res

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        query = """
        CREATE OR REPLACE VIEW de_productivity_report AS (
        SELECT 
           ROW_NUMBER() OVER (ORDER BY SA.region_id) AS id,
           RCS.id as state_id, 
           SA.region_id, 
           SA.vehicle_category_id, 
           HR.id as manager_id, 
           HJ.id as job_id, 
           COUNT(SA.id) as order_count, 
           COUNT(DISTINCT SA.driver_id) as driver_count, 
           CASE 
               WHEN COALESCE(COUNT(DISTINCT SA.driver_id), 0) > 0 
                    AND COUNT(SA.id) IS NOT NULL 
               THEN (CAST(COUNT(SA.id) AS FLOAT) / CAST(COUNT(DISTINCT SA.driver_id) AS FLOAT)) 
               ELSE 0 
           END as productivity, 
           SA.productivity_date 
        FROM (
            SELECT 
                SO.id, 
                SO.region_id, 
                SO.vehicle_category_id, 
                SO.driver_id,
                CASE 
                    WHEN CAST(SO.create_date AS TIME) >= '18:30:00' 
                         AND CAST(SO.create_date AS TIME) <= '23:59:59' 
                    THEN CAST(CAST(SO.create_date AS DATE) + INTERVAL '1 day' AS DATE) 
                    ELSE CAST(SO.create_date AS DATE) 
                END as productivity_date 
            FROM 
                sale_order SO 
            WHERE 
                SO.state != 'cancel'
        ) as SA 
        LEFT JOIN hr_employee HE ON HE.id = SA.driver_id 
        LEFT JOIN hr_employee HR ON HE.parent_id = HR.id 
        LEFT JOIN sales_region R ON SA.region_id = R.id 
        LEFT JOIN res_country_state RCS ON R.state_id = RCS.id 
        LEFT JOIN hr_job HJ ON HR.job_id = HJ.id 
        GROUP BY 
            RCS.id, 
            SA.region_id, 
            SA.vehicle_category_id, 
            HR.id, 
            HJ.id, 
            SA.productivity_date 
        ORDER BY 
            SA.region_id
        )
        """
        self.env.cr.execute(query)

