from odoo import models


class BatchTripFtl(models.Model):
    _inherit = "batch.trip.ftl"

    def write(self, vals):
        res = super(BatchTripFtl, self).write(vals)
        if vals.get('state') == 'finance_approved':
            for rec in self:
                ftl_target_list = self.env['salesperson.target.list'].search([('sales_person_id', '=', rec.sales_person_id.id),
                                                                          ('from_date', '<=', rec.trip_date),
                                                                          ('to_date', '>=', rec.trip_date),
                                                                          ('region_id', '=', rec.region_id.id)])
                if ftl_target_list:
                    for ftl_target in ftl_target_list:
                        ftl_target._compute_sales_person_wise_total_achieved_revenue()
        return res