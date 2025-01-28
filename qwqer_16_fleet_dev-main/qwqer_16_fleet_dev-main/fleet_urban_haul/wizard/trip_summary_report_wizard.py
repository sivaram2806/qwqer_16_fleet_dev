from odoo import fields, models, api
from odoo.exceptions import ValidationError


class TripSummaryReportWizard(models.TransientModel):
    _name = 'trip.summary.report.wizard'
    _description = 'Wizard for generating customer and vendor trip summary report'

    from_date = fields.Date()
    to_date = fields.Date()
    vendor_id = fields.Many2one('res.partner')
    customer_id = fields.Many2one('res.partner')
    region_id = fields.Many2one('sales.region', domain= lambda self:  [("company_id", "=", self.env.company.id)])
    sales_person_id = fields.Many2one('hr.employee')
    action_type = fields.Selection([("customer", "Customer"), ("vendor", "Vendor")], required=True)

    @api.onchange('region_id')
    def onchange_customer_vendor(self):
        """Onchange to update domain filter for vendor and customer id with any change in region id"""
        for rec in self:
            if rec.region_id:
                fleet_service_type = self.env['partner.service.type'].search([('is_fleet_service','=',True)])
                if rec.action_type == 'vendor':
                    return {'domain': {'vendor_id': [('region_id', '=', rec.region_id.id), ('supplier_rank', '>', 0),
                                                     ('service_type_id', 'in', fleet_service_type.ids)],
                                       'sales_person_id': [('region_id', '=', rec.region_id.id)]}}
                elif rec.action_type == 'customer':
                    return {'domain': {'customer_id': [('region_id', '=', rec.region_id.id), ('customer_rank', '>', 0),
                                                       ('service_type_id', 'in', fleet_service_type.ids)],
                                       'sales_person_id': [('region_id', '=', rec.region_id.id)]}}

    def action_vendor_trip_summary(self):
        """Method to generate xlsx report with filtered data"""
        for rec in self:
            report = self.sudo().env.ref('fleet_urban_haul.trip_summary_report_xlsx')
            if rec.from_date > rec.to_date:
                raise ValidationError('From Date must be less than To Date!!!')
            if rec.action_type == 'vendor':
                report.report_file = "Vendor_Trip_Summary"
            elif rec.action_type == 'customer':
                report.report_file = "Customer_Trip_Summary"
        data = {
            'ids': self.env.context.get('active_ids', []),
            'model': 'trip.summary.report.wizard',
        }
        return self.env.ref('fleet_urban_haul.trip_summary_report_xlsx').report_action(self, data=data)
