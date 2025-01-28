# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FleetVehicle(models.Model):
    """This model contains record of vehicle"""
    _name = 'vehicle.pricing.line'
    _description = 'Vehicle Pricing Line'
    _inherit = 'mail.thread'
    _order = 'vehicle_no asc'

    _rec_names_search = ['vehicle_no', 'vehicle_model_id']

    vehicle_no = fields.Many2one("vehicle.vehicle", string="Vehicle Number", required=True)
    vehicle_model_id = fields.Many2one(comodel_name="fleet.vehicle.model", string="Vehicle Model",
                                       related='vehicle_no.vehicle_model_id')
    customer_id = fields.Many2one(comodel_name='res.partner', string="Customer",
                                  domain="['|', ('company_id', '=', False), "
                                         "('company_id', '=', company_id),"
                                         " ('customer_rank', '>', 0)]")
    vendor_id = fields.Many2one(comodel_name='res.partner', string="Vendor",
                                  domain="['|', ('company_id', '=', False),"
                                         " ('company_id', '=', company_id), "
                                         "('supplier_rank', '>', 0)]")
    driver_name = fields.Char(string="Driver Name")
    vehicle_description = fields.Char(string="Vehicle Description")
    vehicle_pricing_id = fields.Many2one('vehicle.pricing', string='Vehicle Pricing', tracking=True,
                                  domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    # Company id for Multi-Company property
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    def name_get(self):
        return [(record.id, f"{record.vehicle_no.vehicle_no} - {record.vehicle_pricing_id.name}")
                for record in self if record.vehicle_no and record.vehicle_no.vehicle_no]

    @api.constrains('vehicle_no', 'customer_id', 'vendor_id', 'vehicle_pricing_id')
    def _check_vehicle_customer_vendor_unique(self):
        vehicle_pricing_list = []
        for rec in self:
            count = rec.search_count(
                [('vehicle_no','=',rec.vehicle_no.vehicle_no),('vehicle_pricing_id', '=', rec.vehicle_pricing_id.id),
                 ('customer_id', '=', rec.customer_id.id),('vendor_id', '=', rec.vendor_id.id)]
            )
            if count > 1:
                vehicle_pricing_list.append(rec.vehicle_pricing_id.name)
                vehicle_pricing_list.append(rec.customer_id.name)
                vehicle_pricing_list.append(rec.vendor_id.name)

            if vehicle_pricing_list:
                str_multiple_vehicle_pricing = ", ".join(vehicle_pricing_list)
                msg = f"Same vehicle pricing with customer and vendor already present in the vehicle:\n{str_multiple_vehicle_pricing}" if len(
                    vehicle_pricing_list) == 1 else f"Same vehicle pricing for customer and vendor is already present in the vehicle:\n{str_multiple_vehicle_pricing}"
                raise UserError(_(msg))

