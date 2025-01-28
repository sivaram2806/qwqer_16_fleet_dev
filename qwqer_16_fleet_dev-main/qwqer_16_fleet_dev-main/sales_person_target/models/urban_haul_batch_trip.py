from odoo import models

class BatchTripUrbanHaul(models.Model):
    _inherit = "batch.trip.uh"

    def write(self, vals):
        res = super(BatchTripUrbanHaul, self).write(vals)
        if vals.get('state') == 'approved':
            for rec in self:
                uh_targets = self.env['salesperson.target.list'].search([('sales_person_id', '=', rec.sales_person_id.id),
                                                                          ('from_date', '<=', rec.trip_date),
                                                                          ('to_date', '>=', rec.trip_date),
                                                                          ('region_id', '=', rec.region_id.id)])
                if uh_targets:
                    for uht in uh_targets:
                        uht._compute_sales_person_wise_total_achieved_revenue()
        return res