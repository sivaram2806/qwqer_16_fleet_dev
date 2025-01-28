# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError


class VehiclePricingLine(models.Model):
    """ The model partner.vehicle.pricing is inherited to make modifications """
    _inherit = 'partner.vehicle.pricing'

    vehicle_pricing_id = fields.Many2one('vehicle.pricing', string='Vehicle Pricing')
    base_cost_hrs = fields.Float(string='Base Cost(Hrs)', digits='Product Price')
    vehicle_model_id = fields.Many2one(comodel_name='fleet.vehicle.model',
                                       related='vehicle_pricing_id.vehicle_model_id')

    @api.onchange('vehicle_pricing_id')
    def _onchange_vehicle_pricing_domain(self):
        """Method for giving domain for vehicle_pricing_id in partner vehicle pricing"""
        vehicle_pricing = []
        if self.partner_id:
            vehicle_pricing_line = self.env['vehicle.pricing.line'].search(['|', ('customer_id', 'in', self.partner_id.ids),
                                                                            ('vendor_id', 'in', self.partner_id.ids)])
            vehicle_pricing_ids = vehicle_pricing_line.mapped('vehicle_pricing_id')
            domain_constraints = ('id', 'in', vehicle_pricing_ids.ids)
            vehicle_pricing.append(domain_constraints)
        domain = {
            'vehicle_pricing_id': vehicle_pricing
        }
        return {'domain': domain}

    @api.constrains('partner_id.frequency', 'trip_frequency')
    def _check_frequency(self):
        for rec in self:
            if rec.partner_id.frequency == 'weekly' and rec.trip_frequency != 'daily':
                raise ValidationError(_('Frequency should be set as daily!'))

    @api.constrains('vehicle_pricing_id')
    def _check_vehicle_pricing_id_unique(self):
        vehicle_pricing_list = []
        for rec in self:
            count = self.search_count(
                [('vehicle_pricing_id', '=', rec.vehicle_pricing_id.id), ('id', '!=', rec.id),
                 ('partner_id', '=', rec.partner_id.id)]
            )
            if count > 0:
                vehicle_pricing_list.append(rec.vehicle_pricing_id.name)

        if vehicle_pricing_list:
            str_multiple_vehicle_pricing = "\n".join(vehicle_pricing_list)
            msg = f"Below vehicle pricing is selected multiple times:\n{str_multiple_vehicle_pricing}" if len(
                vehicle_pricing_list) == 1 else f"Below vehicle pricings are selected multiple times:\n{str_multiple_vehicle_pricing}"
            raise UserError(_(msg))

    def write(self, vals):
        """
        To restrict edit before updating a plan if active trip exists
        @param vals:
        """
        for rec in self:
            batch_trip_uh_ids = self.env['batch.trip.uh.line'].search(
                ['|', ('customer_id', '=', rec.partner_id.id), ('vendor_id', '=', rec.partner_id.id),
                 ('vehicle_pricing_id', '=', rec.vehicle_pricing_id.id),
                 ('batch_trip_uh_id.state', 'not in', ['completed', 'rejected'])])
            if batch_trip_uh_ids:
                raise UserError(_('Not allowed to edit the pricing table when there is an active trip..'))
        return super(VehiclePricingLine, self).write(vals)

    def unlink(self):
        """
        TO check any existing trip present to restrict delete
        """
        for rec in self:
            batch_trip_uh_ids = self.env['batch.trip.uh.line'].search(
                ['|', ('customer_id', '=', rec.partner_id.id), ('vendor_id', '=', rec.partner_id.id),
                 ('vehicle_pricing_id', '=', rec.vehicle_pricing_id.id),
                 ('batch_trip_uh_id.state', 'not in', ['completed', 'rejected'])])
            if batch_trip_uh_ids:
                raise UserError(_('Not allowed to delete the pricing table when there is an active trip..'))
        return super(VehiclePricingLine, self).unlink()
