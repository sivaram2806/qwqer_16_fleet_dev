# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FleetVehiclePricing(models.Model):
    _inherit = 'vehicle.pricing'

    @api.constrains('name')
    def _check_vehicle_no(self):
        for rec in self:
            if rec.name:
                vehicle_pricing_name_normalized = rec.name.replace(" ", "").lower()
                existing_vehicle_pricing = self.env['vehicle.pricing'].search([('id', '!=', rec.id)])

                for line in existing_vehicle_pricing:
                    if line.name:
                        existing_name_normalized = line.name.replace(" ", "").lower()
                        if vehicle_pricing_name_normalized == existing_name_normalized:
                            raise UserError(_('Vehicle pricing with a similar name already exists.'))

    def unlink(self):
        for rec in self:
            daily_trip_ids = self.env['batch.trip.uh.line'].search([('batch_trip_uh_id', '!=', False),
                                                                    ('batch_trip_uh_id.state', 'not in',
                                                                     ('completed', 'rejected')),
                                                                    ('vehicle_pricing_id', '=', rec.id)])
            vehicle_pricing_ids = self.env['vehicle.pricing'].search([('partner_id', '!=', False),
                                                                      ('vehicle_pricing_id', '=', rec.id)])

            if daily_trip_ids:
                raise UserError(_('There is an active trip!!!'))
            elif vehicle_pricing_ids:
                vehicle_pricing = rec.name
                partner = vehicle_pricing_ids.mapped('partner_id.name')
                joined_string = ",".join(partner)
                raise UserError(_(f"{vehicle_pricing} is in {joined_string} pricing!!!"))

        return super(FleetVehiclePricing, self).unlink()

    def action_archive(self):
        for rec in self:
            daily_trip_ids = self.env['batch.trip.uh.line'].search([('batch_trip_uh_id', '!=', False),
                                                                    ('batch_trip_uh_id.state', 'not in',
                                                                     ('completed', 'rejected')),
                                                                    ('vehicle_pricing_id', '=', rec.id)])
            partner_vehicle_pricing_ids = self.env['partner.vehicle.pricing'].search([('partner_id', '!=', False),
                                                                                ('vehicle_pricing_id', '=', rec.id)])

            if daily_trip_ids:
                raise UserError(_('There is an active trip!!!'))

            elif partner_vehicle_pricing_ids:
                vehicle_pricing = rec.name
                partner = partner_vehicle_pricing_ids.mapped('partner_id.name')
                joined_string = ",".join(partner)
                raise UserError(_(f"{vehicle_pricing} is in {joined_string} pricing!!!"))

        return super(FleetVehiclePricing, self).action_archive()

