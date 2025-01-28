# -*- coding: utf-8 -*-

import base64
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date
from . import batch_trip_uh
from lxml import etree
from odoo import SUPERUSER_ID



class ConsolidatedTripSummary(models.Model):
    """The model contain functionality and fields of fetching the daily trip of customer or vendor and creating invoice
    - V13 model name is trip.Summary"""

    _name = 'trip.summary.uh'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Trip Summary'
    _order = 'id desc'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(ConsolidatedTripSummary, self).get_view(view_id=view_id, view_type=view_type, **options)
        doc = etree.XML(res['arch'])
        context = self._context

        if not self.env.user.has_group('fleet.fleet_group_manager') and not self.env.user.has_group(
                'fleet_urban_haul.group_create_edit_consolidate'):
            if view_type == 'form':
                for node_form in doc.xpath("//form"):
                    node_form.set("edit", 'false')
                    node_form.set("create", 'false')
                    node_form.set("delete", 'false')
            if view_type == 'tree':
                for node_form in doc.xpath("//tree"):
                    node_form.set("create", 'false')
                    node_form.set("delete", 'false')
        res['arch'] = etree.tostring(doc)
        return res

    customer_id = fields.Many2one('res.partner', string="Customer",
                                  domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    name = fields.Char(string='Trip Con. Number')
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    vendor_id = fields.Many2one('res.partner', string="Vendor",
                                domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    region_id = fields.Many2one('sales.region', string="Trip Region",
                                domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    trip_summary_line_ids = fields.One2many('trip.summary.line.uh', 'trip_summary_id', string='Trip Summary Line',
                                            copy=False)
    invoice_id = fields.Many2one('account.move', string="Invoice/Bill", copy=False)
    invoice_ids = fields.Many2many('account.move', string="Invoice/Bill References", copy=False)
    total_amount = fields.Float(string="Total", compute='_compute_total_amount', store=True)
    state = fields.Selection([
        ("new", "New"),
        ("draft", "Draft"),
        ("posted", "Posted"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled")
        , ], default="new", string='Status', copy=False, track_visibility='onchange')
    invoice_frequency = fields.Selection(batch_trip_uh.FREQUENCY, default=batch_trip_uh.FREQUENCY[0][0],
                                         string="Invoice Frequency", copy=False)
    partner_type = fields.Selection([
        ("customer", "Customer"),
        ("vendor", "Vendor"),
    ], default="customer", string="Partner Type", copy=False)
    sales_person_id = fields.Many2one('hr.employee', string='Sales Person')

    invoice_count = fields.Integer(string='Count', compute='_compute_invoice_count')
    deduction = fields.Float(string='Deduction', track_visibility='onchange', copy=False)
    additional_charge = fields.Float(string='Additional Charge', track_visibility='onchange', copy=False)
    grand_total = fields.Float(string="Total Amount", compute='_compute_total_amount', store=True)
    additional_charge_comments = fields.Text(string='Additional Charge Comments', copy=False)
    deduction_comments = fields.Text(string='Deduction Comments', copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        """generate sequence for trip summary"""
        company_id = self.env.company.id
        if vals.get('partner_type', 'customer') == 'customer':
            sequence = self.env['ir.sequence'].search(
                [('company_id', '=', company_id), ('code', '=', 'customer.trip.summary.uh')])
            if not sequence:
                sequence = self.env['ir.sequence'].search([('code', '=', 'customer.trip.summary.uh')], limit=1)
                new_sequence = sequence.sudo().copy()
                new_sequence.company_id = company_id
                vals['name'] = new_sequence.next_by_id()
            else:
                vals['name'] = self.env['ir.sequence'].with_company(company_id).next_by_code('customer.trip.summary.uh')
        else:
            sequence = self.env['ir.sequence'].search(
                [('company_id', '=', company_id), ('code', '=', 'vendor.trip.summary.uh')], limit=1)
            if not sequence:
                sequence = self.env['ir.sequence'].search(
                    [('code', '=', 'vendor.trip.summary.uh')])
                new_sequence = sequence.sudo().copy()
                new_sequence.company_id = company_id
                vals['name'] = new_sequence.next_by_id()
            else:
                vals['name'] = self.env['ir.sequence'].with_company(company_id).next_by_code('vendor.trip.summary.uh')

        if vals.get('deduction', 0) > 0:
            if not vals.get('deduction_comments', False):
                raise UserError(_("Please add deduction comment!!!"))
        if vals.get('additional_charge', 0) > 0:
            if not vals.get('additional_charge_comments', False):
                raise UserError(_("Please add additional charge comment!!!"))
        res = super(ConsolidatedTripSummary, self).create(vals)
        res.action_load_trip()

        return res

    def write(self, vals):
        res = super(ConsolidatedTripSummary, self).write(vals)
        for rec in self:
            if rec.deduction > 0:
                if not rec.deduction_comments:
                    raise UserError(_("Please add deduction comment!!!"))
            if rec.additional_charge > 0:
                if not rec.additional_charge_comments:
                    raise UserError(_("Please add additional charge comment!!!"))

        check_vals = ['vendor_id', 'customer_id', 'from_date', 'to_date', 'region_id']
        changed_val = False
        for val in vals:
            if val in check_vals:
                changed_val = True
        if changed_val:
            for rec in self:
                charges = {}
                if rec.deduction > 0:
                    charges.update({'deduction': 0.00, 'deduction_comments': False})
                if rec.additional_charge > 0:
                    charges.update({'additional_charge': 0.00, 'additional_charge_comments': False})
                if charges:
                    rec.write(charges)
                rec.action_load_trip()
        return res

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})

        if self.partner_type == 'customer':
            default['partner_type'] = 'customer'

        else:
            default['partner_type'] = 'vendor'

        return super(ConsolidatedTripSummary, self).copy(default)

    def unlink(self):
        for rec in self:
            if not self.env.user.has_group('fleet.fleet_group_manager'):
                raise UserError(_("You are not allowed to delete the consolidate."))
            if rec.state not in ('new', 'cancelled'):
                raise UserError(_("You cannot delete the consolidate which has been created invoice."))
            if rec.state == 'new':
                if rec.partner_type == 'customer':
                    daily_trip_line_ids = self.env['batch.trip.uh.line'].search(
                        [('batch_trip_uh_id', '!=', False), ('trip_summary_customer_id', '=', rec.id)])
                    # daily_trip_line_ids.mapped('batch_trip_uh_id').write({'invoice_state': 'to_invoice'})
                    daily_trip_line_ids.write({'trip_summary_customer_id': False,
                                               'invoice_state':'to_invoice'})
                else:
                    daily_trip_line_ids = self.env['batch.trip.uh.line'].search(
                        [('batch_trip_uh_id', '!=', False), ('trip_summary_vendor_id', '=', rec.id)])
                    daily_trip_line_ids.write({'trip_summary_vendor_id': False, 'bill_state': 'to_paid'})
        return super(ConsolidatedTripSummary, self).unlink()

    @api.depends('trip_summary_line_ids', 'additional_charge', 'deduction')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.trip_summary_line_ids.mapped('customer_amount'))
            rec.grand_total = rec.total_amount + rec.additional_charge - rec.deduction

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.onchange('customer_id', 'vendor_id')
    def onchange_region(self):
        """it will perform when any change in customer and partner filed it will fetch that customer
         region ,frequency,order_sale_person"""
        for rec in self:
            if rec.customer_id:
                rec.region_id = rec.customer_id.region_id.id
                rec.invoice_frequency = rec.customer_id.frequency
                rec.sales_person_id = rec.customer_id.order_sales_person.id
            if rec.vendor_id:
                rec.region_id = rec.vendor_id.region_id.id
                rec.invoice_frequency = rec.vendor_id.frequency
                rec.sales_person_id = rec.vendor_id.order_sales_person.id

    def action_load_trip(self):
        """the function will fetch all the trip created for
        the customer and vendor within the date limit"""
        for rec in self:
            if rec.state != 'new':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_("consolidate is in %s state.Please Refresh" % (state)))
            rec.trip_summary_line_ids = False

            if rec.partner_type == 'customer':
                batch_trip_line_ids = self.env['batch.trip.uh.line'].search(
                    [('batch_trip_uh_id', '!=', False), ('invoice_state', '=', 'to_invoice'),
                     ('batch_trip_uh_id.state', '=', 'approved'),
                     ('customer_id', '=', rec.customer_id.id), ('region_id', '=', rec.region_id.id),
                     ('trip_date', '<=', rec.to_date), ('trip_date', '>=', rec.from_date)])

            else:
                batch_trip_line_ids = self.env['batch.trip.uh.line'].search(
                    [('batch_trip_uh_id', '!=', False), ('bill_state', '=', 'to_paid'),
                     ('batch_trip_uh_id.state', '=', 'approved'),
                     ('vendor_id', '=', rec.vendor_id.id), ('region_id', '=', rec.region_id.id),
                     ('trip_date', '<=', rec.to_date), ('trip_date', '>=', rec.from_date)])

            if not batch_trip_line_ids:
                raise UserError(_("No trips to Load!!!"))

            vehicle_ids = batch_trip_line_ids.mapped('vehicle_pricing_line_id')
            for vehicle in vehicle_ids:
                vehicle_lines = batch_trip_line_ids.filtered(lambda s: s.vehicle_pricing_line_id.id == vehicle.id)
                start_time = sum(vehicle_lines.mapped('start_time')) or 0.0
                end_time = sum(vehicle_lines.mapped('end_time')) or 0.0
                total_time = end_time - start_time
                start_km = sum(vehicle_lines.mapped('start_km')) or 0.0
                end_km = sum(vehicle_lines.mapped('end_km')) or 0.0
                total_km = end_km - start_km

                if rec.partner_type == 'customer':
                    customer_amount = 0.0
                    if vehicle_lines and vehicle_lines[0].calculation_frequency == 'monthly':
                        if rec.customer_id.partner_vehicle_pricing_ids:
                            customer_vehicle_id = self.env['partner.vehicle.pricing'].search(
                                [('partner_id', '=', rec.customer_id.id),
                                 ('vehicle_pricing_id', '=', vehicle.vehicle_pricing_id.id)], limit=1)

                            if customer_vehicle_id:
                                customer_km_cost = 0.0
                                customer_hour_cost = 0.0
                                if total_km:
                                    if total_km <= customer_vehicle_id.base_dist:
                                        customer_km_cost = customer_vehicle_id.base_cost or 0.0
                                    else:
                                        customer_km_cost = (((total_km - customer_vehicle_id.base_dist) *
                                                             customer_vehicle_id.charge_per_km) +
                                                            customer_vehicle_id.base_cost) or 0.0
                                if total_time:
                                    if total_time <= customer_vehicle_id.base_hrs:
                                        customer_hour_cost = customer_vehicle_id.base_cost_hrs or 0.0
                                    else:
                                        customer_hour_cost = (((total_time - customer_vehicle_id.base_hrs) *
                                                               customer_vehicle_id.additional_hrs) +
                                                              customer_vehicle_id.base_cost_hrs) or 0.0
                                customer_amount = (customer_km_cost + customer_hour_cost)

                    elif vehicle_lines and vehicle_lines[0].calculation_frequency == 'daily':
                        customer_amount = sum(vehicle_lines.mapped('customer_amount')) or 0.0

                    values = {
                        'vehicle_pricing_line_id': vehicle.id,
                        'calculation_frequency': vehicle_lines and vehicle_lines[0].calculation_frequency,
                        'start_time': start_time,
                        'end_time': end_time,
                        'start_km': start_km,
                        'end_km': end_km,
                        'customer_amount': customer_amount,
                        'batch_trip_uh_line_ids': [(6, 0, vehicle_lines.ids)]
                    }
                    rec.write({'trip_summary_line_ids': [(0, 0, values)]})
                    vehicle_lines.write({'trip_summary_customer_id': rec.id,
                                         'invoice_state': 'invoiced'})
                    # vehicle_lines.mapped('batch_trip_uh_id').write({'invoice_state': 'invoiced'})

                else:
                    vendor_amount = 0.0
                    if vehicle_lines and vehicle_lines[0].vendor_calculation_frequency == 'monthly':
                        if rec.vendor_id.partner_vehicle_pricing_ids:
                            vendor_vehicle_id = self.env['partner.vehicle.pricing'].search(
                                [('partner_id', '=', rec.vendor_id.id),
                                 ('vehicle_pricing_id', '=', vehicle.vehicle_pricing_id.id)], limit=1)
                            if vendor_vehicle_id:
                                vendor_km_cost = 0.0
                                vendor_hour_cost = 0.0
                                if total_km:
                                    if total_km <= vendor_vehicle_id.base_dist:
                                        vendor_km_cost = vendor_vehicle_id.base_cost or 0.0
                                    else:
                                        vendor_km_cost = (((total_km - vendor_vehicle_id.base_dist) *
                                                           vendor_vehicle_id.charge_per_km) +
                                                          vendor_vehicle_id.base_cost) or 0.0
                                if total_time:
                                    if total_time <= vendor_vehicle_id.base_hrs:
                                        vendor_hour_cost = vendor_vehicle_id.base_cost_hrs or 0.0
                                    else:
                                        vendor_hour_cost = (((total_time - vendor_vehicle_id.base_hrs) *
                                                             vendor_vehicle_id.additional_hrs) +
                                                            vendor_vehicle_id.base_cost_hrs) or 0.0
                                vendor_amount = vendor_km_cost + vendor_hour_cost

                    elif vehicle_lines and vehicle_lines[0].vendor_calculation_frequency == 'daily':
                        vendor_amount = sum(vehicle_lines.mapped('vendor_amount')) or 0.0

                    values = {
                        'vehicle_pricing_line_id': vehicle.id,
                        'calculation_frequency': vehicle_lines and vehicle_lines[0].vendor_calculation_frequency,
                        'start_time': start_time,
                        'end_time': end_time,
                        'start_km': start_km,
                        'end_km': end_km,
                        'customer_amount': vendor_amount,
                        'batch_trip_uh_line_ids': [(6, 0, vehicle_lines.ids)]
                    }
                    rec.write({'trip_summary_line_ids': [(0, 0, values)]})
                    vehicle_lines.write({'trip_summary_vendor_id': rec.id, 'bill_state': 'paid'})

    def action_create_invoice(self):
        """perform to create invoice to customer"""
        for rec in self:
            if rec.state != 'new':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_("consolidate is in %s state.Please Refresh" % (state)))

            if not rec.trip_summary_line_ids:
                raise UserError(_("There is no lines!!!"))

            count = self.env['batch.trip.uh.line'].search_count([('trip_summary_customer_id', '=', rec.id)]) or 0.0
            line_list = []
            if rec.customer_id.fleet_hsn_id:
                product = rec.customer_id.fleet_hsn_id.id
            else:
                product = rec.company_id.fleet_invoice_product_id.id
            if not rec.customer_id.vehicle_invoice_tax_ids.ids:
                raise UserError(_("Please add fleet tax in %s customer!!!") % rec.customer_id.name)
            analytic_account_ids = rec.customer_id.region_id.analytic_account_id.id
            new_dict = {
                'product_id': product,
                'name': 'Charges towards the fleet services b/w %s to %s \nTotal no. of trips : %s'
                        % (rec.from_date.strftime('%d/%m/%y'), rec.to_date.strftime('%d/%m/%y'), count),
                'price_unit': rec.grand_total,
                'tax_ids': [(6, 0, rec.customer_id.vehicle_invoice_tax_ids.ids)],
                'analytic_distribution': {
                    analytic_account_ids: 100
                },
            }
            line_list.append((0, 0, new_dict))
            state_journal = self.env['state.journal'].search(
                [('state_id', '=', rec.customer_id.region_id.state_id.id), ('company_id', '=', rec.company_id.id)])
            if not state_journal.fleet_journal_id:
                raise UserError(
                    _("Please add fleet journal in %s state!!!") % rec.customer_id.region_id.state_id.name)

            invoices = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'journal_id': state_journal.fleet_journal_id.id,
                'invoice_date': date.today(),
                'partner_id': rec.customer_id.id,
                'state': 'draft',
                'vehicle_customer_consolidate_id': rec.id,
                'invoice_line_ids': line_list,
                'invoice_origin': rec.name,
                'company_id': rec.company_id.id,
                'service_type_id': rec.customer_id.service_type_id.id,
                'segment_id': rec.customer_id.segment_id.id,
                'region_id': rec.customer_id.region_id.id if rec.customer_id.region_id else False,
                'sales_person_id': rec.customer_id.order_sales_person.id if rec.customer_id.order_sales_person else False,

            })
            rec.invoice_id = invoices.id
            rec.invoice_ids = [(4, invoices.id, False)]
            rec.state = 'draft'
            tree_view = self.env.ref('account.view_invoice_tree')
            form_view = self.env.ref('account.view_move_form')
            context = dict(self._context)
            context.update({'from_fleet': True})
            return {
                'name': _('Invoices'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
                'domain': [('id', '=', invoices.id)],
                'context': context,
                'target': 'current',
            }

    def action_create_bill(self):
        """perform to create a bill for vendor"""
        for rec in self:
            if rec.state != 'new':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_("consolidate is in %s state.Please Refresh" % (state)))
            if not rec.trip_summary_line_ids:
                raise UserError(_("There is no lines!!!"))

            count = self.env['batch.trip.uh.line'].search_count([('trip_summary_vendor_id', '=', rec.id)])
            line_list = []
            if rec.vendor_id.fleet_hsn_id:
                product = rec.vendor_id.fleet_hsn_id.id
            else:
                product = rec.company_id.fleet_invoice_product_id.id
            if not rec.vendor_id.vehicle_invoice_tax_ids.ids:
                raise UserError(_("Please add fleet tax in %s vendor!!!") % (rec.vendor_id.name))

            fleet_bill_account_id = rec.company_id.fleet_bill_account_id.id
            analytic_account_ids = rec.vendor_id.region_id.analytic_account_id.id
            new_dict = {
                'product_id': product,
                'name': 'Charges towards the fleet services b/w %s to %s \nTotal no. of trips : %s'
                        % (rec.from_date.strftime('%d/%m/%y'), rec.to_date.strftime('%d/%m/%y'), count),
                'price_unit': rec.grand_total,
                'tax_ids': [(6, 0, rec.vendor_id.vehicle_invoice_tax_ids.ids)],
                'analytic_distribution': {
                    analytic_account_ids: 100
                },
                'account_id': fleet_bill_account_id,
            }
            line_list.append((0, 0, new_dict))
            state_journal = self.env['state.journal'].search(
                [('state_id', '=', rec.vendor_id.region_id.state_id.id), ('company_id', '=', rec.company_id.id)])
            if not state_journal.vendor_bill_journal_id:
                raise UserError(
                    _("Please add fleet bill journal in %s state!!!") % (rec.vendor_id.region_id.state_id.name))

            # payment_mode_id = self.env['payment.mode'].search([('is_credit_payment', '=', True)], limit=1)

            bill = self.env['account.move'].create({
                'move_type': 'in_invoice',
                'journal_id': state_journal.vendor_bill_journal_id.id,
                'invoice_date': date.today(),
                'partner_id': rec.vendor_id.id,
                'state': 'draft',
                'vehicle_customer_consolidate_id': rec.id,
                'invoice_line_ids': line_list,
                'invoice_origin': rec.name,
                'company_id': rec.company_id.id,
                'service_type_id': rec.vendor_id.service_type_id.id,
                'segment_id': rec.vendor_id.segment_id.id,
            })
            rec.invoice_id = bill.id
            rec.invoice_ids = [(4, bill.id, False)]
            rec.state = 'draft'
            tree_view = self.env.ref('account.view_invoice_tree')
            form_view = self.env.ref('account.view_move_form')
            context = dict(self._context)
            context.update({'from_fleet': True})
            return {
                'name': _('Bill'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
                'domain': [('id', '=', bill.id)],
                'context': context,
                'target': 'current',
            }

    def action_view_invoice(self):
        """to view the invoice through smart button in conso trip summary view"""
        for rec in self:
            context = dict(self._context)
            context.update({'from_fleet': True})

            if rec.partner_type == 'customer':
                name = 'Invoices'
            else:
                name = 'Bill'

            return {
                'name': _(name),
                'res_model': 'account.move',
                'view_mode': 'list,form',
                'context': context,
                'domain': [('id', 'in', rec.invoice_ids.ids)],
                'target': 'current',
                'type': 'ir.actions.act_window',
            }

    def print_xlsx(self):
        """this function used to print xlsx report"""
        for rec in self:
            pass
            data = {
                'ids': self.env.context.get('active_ids', []),
                'model': 'trip.summary.uh',
            }
            report = self.sudo().env.ref('fleet_urban_haul.consolidated_trip_report_xlsx')
            if rec.partner_type == 'customer':
                report.report_file = "Customer_Trip_%s_to_%s" % (self.from_date or '', self.to_date or '')
            else:
                report.report_file = "Vendor_Trip_%s_to_%s" % (self.from_date or '', self.to_date or '')
            return report.report_action(self, data=data)

    def action_mail_send_to_partner(self):
        """this function used to send mail to customer  and vendor about the consolidated trip summary"""
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']

        try:
            compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        except ValueError:
            compose_form_id = False

        batch_trip_report_id = self.env.ref('fleet_urban_haul.consolidated_trip_report_xlsx')
        generated_report = self.env['ir.actions.report']._render_xlsx(batch_trip_report_id,[self.id], data=self.env.context)
        data_record = base64.b64encode(generated_report[0])

        ir_values = {
            'name': 'Trip Summary.xlsx',
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/vnd.ms-excel',
            'res_model': 'trip.summary.uh',
        }
        attachment = self.env['ir.attachment'].sudo().create(ir_values)
        if self.partner_type == 'customer':
            email_template = self.env.ref(
                'fleet_urban_haul.consolidated_customer_trip_send_to_customer_email_template')
        else:
            email_template = self.env.ref(
                'fleet_urban_haul.consolidated_vendor_trip_send_to_customer_email_template')
        email_template.write({'attachment_ids': [(6, 0, [attachment.id])]})

        ctx = {
            'default_model': 'trip.summary.uh',
            'default_res_id': self.ids[0],
            'default_use_template': bool(email_template.id),
            'default_template_id': email_template.id,
            'default_composition_mode': 'comment',
            'default_send_mail_bool': True,
            'mark_so_as_sent': True,
            'force_email': True
        }

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'views_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
        pass

    def cancel_consolidate(self):
        for rec in self:
            if rec.state != 'new':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_("consolidate is in %s state.Please Refresh" % (state)))
            if rec.partner_type == 'customer':
                daily_trip_line_ids = self.env['batch.trip.uh.line'].search(
                    [('batch_trip_uh_id', '!=', False), ('trip_summary_customer_id', '=', rec.id)])
                # daily_trip_line_ids.mapped('batch_trip_uh_id').write({'invoice_state': 'to_invoice'})
                daily_trip_line_ids.write({'trip_summary_customer_id': False,
                                           'invoice_state': 'to_invoice'})
            else:
                daily_trip_line_ids = self.env['batch.trip.uh.line'].search(
                    [('batch_trip_uh_id', '!=', False), ('trip_summary_vendor_id', '=', rec.id)])
                daily_trip_line_ids.write({'trip_summary_vendor_id': False, 'bill_state': 'to_paid'})
            rec.state = 'cancelled'

    def update_sales_person(self):
        for rec in self:
            rec.sales_person_id = rec.customer_id.order_sales_person.id

    def update_invoice_reference(self):
        for rec in self:
            invoices = self.env['account.move'].search([('vehicle_customer_consolidate_id', '=', rec.id)])
            rec.invoice_ids = [(4, invoice.id, False) for invoice in invoices]

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # if self.env.user.id != SUPERUSER_ID:
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    args.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    args.append(('region_id', 'in', []))
        res = super(ConsolidatedTripSummary, self).search(args, offset, limit, order, count=count)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    domain.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    domain.append(('region_id', 'in', []))
        return super(ConsolidatedTripSummary, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)


class TripSummaryLine(models.Model):
    _name = 'trip.summary.line.uh'
    _description = 'Trip Summary Line'

    name = fields.Char(string='Ref. Number')
    trip_summary_id = fields.Many2one('trip.summary.uh', ondelete='cascade', index=True, copy=False)
    vehicle_pricing_line_id = fields.Many2one('vehicle.pricing.line', string='Vehicle Number')
    from_date = fields.Date(string="From Date", related='trip_summary_id.from_date', store=True)
    to_date = fields.Date(string="To Date", related='trip_summary_id.to_date', store=True)
    customer_id = fields.Many2one('res.partner', string="Customer", related='trip_summary_id.customer_id', store=True)
    vehicle_model_id = fields.Many2one('fleet.vehicle.model',
                                       related='vehicle_pricing_line_id.vehicle_no.vehicle_model_id', store=True)
    region_id = fields.Many2one('sales.region', string="Region", related='trip_summary_id.region_id', store=True)
    calculation_frequency = fields.Selection(batch_trip_uh.CALCULATION_FREQUENCY, string="Calculation Method",
                                             default=batch_trip_uh.CALCULATION_FREQUENCY[0][0], copy=False)
    start_time = fields.Float(string="Start Time", default=9.0)
    end_time = fields.Float(string="End Time", default=18.0)
    total_time = fields.Float(string="Total Time", compute='_compute_total_time', store=True)
    start_km = fields.Float(string="Start Odo")
    end_km = fields.Float(string="End Odo")
    total_km = fields.Float(string="Total Odo", compute='_compute_total_km', store=True)
    customer_amount = fields.Float(digits='Product Price', string='Amount')
    invoice_frequency = fields.Selection(batch_trip_uh.FREQUENCY, default=batch_trip_uh.FREQUENCY[0][0],
                                         copy=False, string="Invoice Frequency",
                                         related='trip_summary_id.invoice_frequency', store=True)
    batch_trip_uh_line_ids = fields.Many2many('batch.trip.uh.line', 'model_id', 'batch_trip_uh_id', copy=False,
                                              string='Trip Details')
    price_config_id = fields.Many2one('vehicle.pricing', string='Vehicle Pricing', store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        res = super(TripSummaryLine, self).create(vals)
        """generate sequence for trip summary line"""
        company_id = self.env.company.id
        if res.trip_summary_id.partner_type == 'customer':
            sequence = self.env['ir.sequence'].search(
                [('company_id', '=', company_id), ('code', '=', 'customer.trip.summary.line.uh')])
            if not sequence:
                sequence = self.env['ir.sequence'].search([('code', '=', 'customer.trip.summary.line.uh')], limit=1)
                new_sequence = sequence.sudo().copy()
                new_sequence.company_id = company_id
                res.name = new_sequence.next_by_id()
            else:
                res.name = self.env['ir.sequence'].with_company(company_id).next_by_code(
                    'customer.trip.summary.line.uh')
        else:
            sequence = self.env['ir.sequence'].search(
                [('company_id', '=', company_id), ('code', '=', 'vendor.trip.summary.line.uh')])
            if not sequence:
                sequence = self.env['ir.sequence'].search([('code', '=', 'vendor.trip.summary.line.uh')], limit=1)
                new_sequence = sequence.sudo().copy()
                new_sequence.company_id = company_id
                res.name = self.env['ir.sequence'].next_by_code('vendor.trip.summary.line.uh')
            else:
                res.name = self.env['ir.sequence'].next_by_code('vendor.trip.summary.line.uh')
        if not res.price_config_id:
            res.onchange_vehicle_no()
        return res

    @api.onchange('vehicle_pricing_line_id')
    def onchange_vehicle_no(self):
        for rec in self:
            rec.price_config_id = rec.vehicle_pricing_line_id.vehicle_pricing_id.id

    @api.depends('start_km', 'end_km')
    def _compute_total_km(self):
        for rec in self:
            rec.total_km = 0.0
            if rec.end_km:
                rec.total_km = rec.end_km - rec.start_km

    @api.depends('start_time', 'end_time')
    def _compute_total_time(self):
        for rec in self:
            rec.total_time = rec.end_time - rec.start_time

    def unlink(self):
        for rec in self:
            if rec.trip_summary_id.state == 'new':
                if rec.batch_trip_uh_line_ids:
                    for line in rec.batch_trip_uh_line_ids:
                        if rec.trip_summary_id.partner_type == 'customer':
                            line.trip_summary_customer_id = False
                            line.invoice_state = 'to_invoice'
                        else:
                            line.trip_summary_vendor_id = False
                            line.bill_state = 'to_paid'
            else:
                raise UserError('You can remove lines only in New state')
        return super(TripSummaryLine, self).unlink()
