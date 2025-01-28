# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    """ The model res_partner is inherited to make modifications """
    _inherit = 'res.partner'

    vehicle_pricing_id = fields.Many2one('vehicle.pricing', string="Vehicle Pricing",
                                         domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    vehicle_invoice_tax_ids = fields.Many2many('account.tax', 'vehicle_invoice_tax',
                                               'partner1_id', 'tax1_id', string='Fleet Tax',
                                               domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    uh_trip_count = fields.Integer(string='Urban Haul Trip Count', compute='_compute_uh_trip_count')
    is_ftl_customer = fields.Boolean(default=False)



    def _compute_uh_trip_count(self):
        for rec in self:
            rec.uh_trip_count = 0
            if rec.customer_rank > 0:
                rec.uh_trip_count = self.env['batch.trip.uh'].search_count([('customer_id', '=', rec.id)])
            else:
                rec.uh_trip_count = self.env['batch.trip.uh'].search_count(
                    [('batch_trip_uh_line_ids.vendor_id', '=', rec.id)])

    def action_view_daily_trips(self):
        for rec in self:
            return {
                'name': _('Daily Trip'),
                'res_model': 'batch.trip.uh',
                'view_mode': 'list,form',
                'context': {'create': False, 'edit': False},
                'domain': ['|', ('customer_id', '=', rec.id), ('batch_trip_uh_line_ids.vendor_id', '=', rec.id)],
                'target': 'current',
                'type': 'ir.actions.act_window',
            }

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if self.env.context.get('res_partner_form', False):
            for rec in res:
                rec._log_pricing_changes(vals)
                rec._check_frequency_change(vals)
        return res


    def write(self, vals):
        if self.env.context.get('res_partner_form', False):
            for rec in self:
                rec._log_pricing_changes(vals)
                rec._check_frequency_change(vals)
        return super().write(vals)

    def _log_pricing_changes(self, vals):
        if 'vehicle_pricing_line_ids' in vals:
            for line in vals['vehicle_pricing_line_ids']:
                if line[0] == 1 and line[2]:
                    msg_list = []
                    vehicle_pricing = self.env['vehicle.pricing.line'].browse(line[1])
                    for field, value in line[2].items():
                        field_string = self.env['vehicle.pricing.line']._fields[field].string
                        current_value = getattr(vehicle_pricing, field)
                        new_value = self.env['vehicle.pricing'].browse(value).name if field == 'vehicle_pricing_id' else value
                        msg_list.append(f'{field_string} changed from {current_value} to {new_value}')
                    msg = f'Vehicle pricing {vehicle_pricing.vehicle_pricing_id.name}: ' + ", ".join(msg_list)
                    self.message_post(body=msg)
                elif line[0] == 0:
                    vehicle_pricing = self.env['vehicle.pricing'].browse(line[2]['vehicle_pricing_id'])
                    msg = f'Vehicle pricing {vehicle_pricing.name} added'
                    self.message_post(body=msg)
                elif line[0] == 2:
                    vehicle_pricing = self.env['vehicle.pricing.line'].browse(line[1])
                    msg = f'Vehicle pricing {vehicle_pricing.vehicle_pricing_id.name} removed'
                    self.message_post(body=msg)

        if 'vehicle_invoice_tax_ids' in vals:
            values_before = self.vehicle_invoice_tax_ids.mapped('name') if self.vehicle_invoice_tax_ids else []
            values_after = self.env['account.tax'].search(
                [('id', 'in', vals.get("vehicle_invoice_tax_ids")[0][-1])]).mapped("name")
            if values_after:
                if values_before:
                    msg = f'Fleet Invoice Tax changed from {values_before} to {values_after}'
                else:
                    msg = f'Fleet Invoice Tax {values_after} added'

                self.message_post(body=msg)

    def _check_frequency_change(self, vals):
        if 'frequency' in vals:
            customer_active_trips = self.env['batch.trip.uh'].search([
                ('customer_id', '=', self.id),
                ('state', 'not in', ['completed', 'rejected'])
            ])
            if customer_active_trips:
                raise UserError(_('Some trips are active for this customer!'))
            vendor_active_trips = self.env['batch.trip.uh.line'].search([
                ('vendor_id', '=', self.id),
                ('batch_trip_uh_id.state', 'not in', ['completed', 'rejected'])
            ])
            if vendor_active_trips:
                raise UserError(_('Some trips are active for this vendor!'))

    def action_save(self):
        return {'type': 'ir.actions.act_window_close'}
