# -*- coding: utf-8 -*-
import base64

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from lxml import etree
from odoo import SUPERUSER_ID


class FtlTripSummary(models.Model):
    """
        Model contains records from trip summary/consolidated customer trip, #V13_model name: trip.summary
        """
    _name = 'trip.summary.ftl'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'ftl consolidate trip summary'
    _order = 'id desc'

    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
    name = fields.Char(string='Trip Con. Number')
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    customer_id = fields.Many2one('res.partner', string="Customer",
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    vendor_id = fields.Many2one('res.partner', string="Vendor",
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    region_id = fields.Many2one('sales.region', string="Trip Region")
    trip_summary_ftl_line_ids = fields.One2many('trip.summary.ftl.line', 'trip_summary_ftl_id',
                                                 string='Trip Summary FTL Line', copy=False)
    invoice_id = fields.Many2one('account.move', string="Invoice/Bill", copy=False)
    invoice_ids = fields.Many2many('account.move', string="Invoice/Bill References", copy=False)
    total_amount = fields.Float(string="Total", compute='_compute_total_amount', store=True)
    state = fields.Selection([("new", "New"),
                              ("draft", "Draft"),
                              ("posted", "Posted"),
                              ("paid", "Paid"),
                              ("cancelled", "Cancelled"), ],
                             default="new", string='Status', copy=False, tracking=True)
    sales_person_id = fields.Many2one('hr.employee', string='Sales Person')
    invoice_count = fields.Integer(string='Count', compute='_compute_invoice_count')
    deduction = fields.Float(string='Deduction', tracking=True, copy=False)
    additional_charge = fields.Float(string='Additional Charge', tracking=True, copy=False)
    grand_total = fields.Float(string="Total Amount", compute='_compute_total_amount', store=True)
    additional_charge_comments = fields.Text(string='Additional Charge Comments', copy=False)
    deduction_comments = fields.Text(string='Deduction Comments', copy=False)
    amount_alert_bool = fields.Boolean(string='Amount Alert Bool', compute='_compute_amount_alert_bool', default=False)
    work_order_ids = fields.Many2many('work.order', string='Work Order(s)')
    work_order_amount = fields.Float(string='Work Order Amount')
    work_order_shipping_address = fields.Text(string='Work Order Shipping Address')

    def get_view(self, view_id=None, view_type='form', **options):
        """extend to disabling  edit and create action if the user is no the group_ftl_create_edit_consolidate group"""
        result = super(FtlTripSummary, self).get_view(view_id=view_id, view_type=view_type, **options)
        doc = etree.XML(result['arch'])

        if not self.env.user.has_group('fleet_ftl.group_ftl_create_edit_consolidate'):
            if view_type == 'form':
                for node_form in doc.xpath("//form"):
                    node_form.set("edit", 'false')
                    node_form.set("create", 'false')
                    node_form.set("delete", 'false')
            if view_type == 'tree':
                for node_form in doc.xpath("//tree"):
                    node_form.set("create", 'false')
                    node_form.set("delete", 'false')
        result['arch'] = etree.tostring(doc)
        return result

    @api.model
    def create(self, vals):
        # adding the sequence to the name field
        company_id = self.env.company.id
        sequence = self.env['ir.sequence'].search(
            [('company_id', '=', company_id), ('code', '=', 'trip.summary.ftl')])
        if not sequence:
            sequence = self.env['ir.sequence'].search([('code', '=', 'trip.summary.ftl')], limit=1)
            new_sequence = sequence.sudo().copy()
            new_sequence.company_id = company_id
            vals['name'] = new_sequence.next_by_id()
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('trip.summary.ftl')
        # validating is description is added to the additional charges fields
        if vals.get('deduction', 0) > 0:
            if not vals.get('deduction_comments', False):
                raise UserError(_("Please add deduction comment!!!"))
        if vals.get('additional_charge', 0) > 0:
            if not vals.get('additional_charge_comments', False):
                raise UserError(_("Please add additional charge comment!!!"))

        filters_vals = {'customer_id': int(vals.get('customer_id')),
                        'region_id': int(vals.get('region_id')),
                        'from_date': vals.get('from_date'),
                        'to_date': vals.get('to_date'),
                        'work_order_id': vals.get('work_order_ids')[-1][-1]
                        }
        res = super(FtlTripSummary, self).create(vals)
        # loading trip to consolidate on save
        if filters_vals:
            res.load_ftl_trip(filters_vals)
        return res

    def write(self, vals):
        res = super(FtlTripSummary, self).write(vals)
        for rec in self:
            is_filter_changed = False
            # validating is description is added to the additional charges fields
            if rec.deduction > 0:
                if not rec.deduction_comments:
                    raise UserError(_("Please add deduction comment!!!"))
            if rec.additional_charge > 0:
                if not rec.additional_charge_comments:
                    raise UserError(
                        _("Please add additional charge comment!!!"))

            filters_vals = {'customer_id': int(rec.customer_id),
                            'region_id': int(rec.region_id),
                            'from_date': rec.from_date,
                            'to_date': rec.to_date,
                            'work_order_id': rec.work_order_ids.ids
            }
            # loading trip to consolidate on write if filter values are changed
            for key, val in vals.items():
                if key in filters_vals:
                    filters_vals[key] = val
                    is_filter_changed = True
            if is_filter_changed:
                rec.load_ftl_trip(filters_vals)

        return res

    @api.depends('work_order_amount', 'grand_total')
    def _compute_amount_alert_bool(self):
        """computing alert_bool field to show or hide amount alert"""
        for rec in self:
            if rec.work_order_amount and rec.grand_total:
                if rec.work_order_amount != rec.grand_total:
                    rec.amount_alert_bool = True
                else:
                    rec.amount_alert_bool = False
            elif rec.work_order_amount and rec.total_amount:
                if rec.grand_total == 0 or 0.00:
                    rec.amount_alert_bool = True
            else:
                rec.amount_alert_bool = False
        return True

    @api.depends('trip_summary_ftl_line_ids', 'additional_charge', 'deduction')
    def _compute_total_amount(self):
        """computing the grand_total field """
        for rec in self:
            rec.total_amount = sum(
                rec.trip_summary_ftl_line_ids.mapped('total_lines_amount'))
            rec.grand_total = (rec.total_amount + rec.additional_charge
                               - rec.deduction)

    @api.onchange('work_order_ids')
    def onchange_work_order(self):
        """setting ,work_order_shipping_address,work_order_amount in change work order"""
        for rec in self:
            if rec.work_order_ids:
                rec.work_order_shipping_address = rec.work_order_ids[0].shipping_address
                rec.work_order_amount = sum([item.total_amount for item in rec.work_order_ids])

    @api.onchange('customer_id')
    def onchange_region(self):
        """setting region on change customer"""
        for rec in self:
            if rec.customer_id:
                rec.region_id = rec.customer_id.region_id.id
                rec.sales_person_id = rec.customer_id.order_sales_person.id

    def cancel_ftl_consolidate(self):
        """function to canceling the consolidate trip/trip summary"""
        for rec in self:
            # validating the sate before cancellation only all cancellation in new state
            if rec.state != 'new':
                state = rec.state and dict(rec._fields['state'].selection).get(
                    rec.state) or ''
                raise UserError(
                    _('Consolidate is in %s state.Please Refresh' % state))
            # resetting related  trip and consolidated trip/ trip summary fields
            daily_trip = self.env['batch.trip.ftl'].search(
                [('trip_summary_ftl_id', '=', rec.id)])
            daily_trip.write({'invoice_state': 'to_invoice', 'trip_summary_ftl_id': False})
            rec.state = 'cancelled'

    def action_view_ftl_invoice(self):
        """function to render invoice view"""
        for rec in self:
            context = dict(self._context)
            context.update({'from_fleet': True, 'create': False})
            return {
                'name': _('Invoices'),
                'res_model': 'account.move',
                'view_mode': 'list,form',
                'context': context,
                'domain': [('id', 'in', rec.invoice_ids.ids)],
                'target': 'current',
                'type': 'ir.actions.act_window',
            }

    def unlink(self):
        """function to deleting consolidate"""
        for rec in self:
            # resetting related  trip and  fields
            if rec.state not in ('new', 'cancelled'):
                raise UserError(_("You cannot delete the consolidate which has been created invoice."))
            elif not self.env.user.has_group('fleet.fleet_group_manager'):
                raise UserError(_("You are not allowed to delete the work order."))
            else:
                daily_trip = self.env['batch.trip.ftl'].search(
                    [('trip_summary_ftl_id', '=', rec.id)])
                daily_trip.write({'invoice_state': 'to_invoice', 'trip_summary_ftl_id': False})
        return super(FtlTripSummary, self).unlink()

    def load_ftl_trip(self, vals):
        """
        function to load trips form batch.trip.ftl based on the filters
        @params customer_id:
        @params region_id:
        @params from_date:
        @params to_date:
        @params work_order_id:
        """
        for rec in self:
            rec.write({'trip_summary_ftl_line_ids': [(5, 0, 0)]})
            filters = [('invoice_state', '=', 'to_invoice'),
                       ('state', '=', 'completed'),
                       ('customer_id', '=', vals['customer_id']),
                       ('region_id', '=', vals['region_id']),
                       ('trip_date', '<=', vals['to_date']),
                       ('trip_date', '>=', vals['from_date']),
                       ('work_order_id', 'in', vals['work_order_id'])]
            batch_trip = self.env['batch.trip.ftl'].search(filters)
            if not batch_trip:
                raise UserError(_("No Trips To Load!!!"))
            for trip in batch_trip:
                values = {
                    'trip_no': trip.name,
                    'trip_date': trip.trip_date,
                    'total_lines_km': trip.total_km or 0.0,
                    'total_lines_amount': trip.total_amount or 0.0,
                    'work_order_id': trip.work_order_id.id,
                    'ftl_batch_trip_id': trip.id
                }
                rec.write({'trip_summary_ftl_line_ids': [(0, 0, values)]})
                trip.write({'trip_summary_ftl_id': rec.id, 'invoice_state': 'invoiced'})

    def action_create_ftl_invoice(self):
        """function for creating consolidated invoice for the trip from batch.trip.ftl in lines"""
        for rec in self:
            if rec.state != 'new':
                state = rec.state and dict(rec._fields['state'].selection).get(
                    rec.state) or ''
                raise UserError(
                    _('Consolidate is in %s state.Please Refresh' % state))
            if not rec.trip_summary_ftl_line_ids:
                raise UserError(_("There is no lines!!!"))

            count = self.env['batch.trip.ftl'].search_count(
                [('trip_summary_ftl_id', '=', rec.id)]) or 0.0
            line_list = []
            if rec.customer_id.fleet_hsn_id:
                product_id = rec.customer_id.fleet_hsn_id.id
            else:
                product_id = self.company_id.fleet_invoice_product_id.id
            if not rec.customer_id.vehicle_invoice_tax_ids.ids:
                raise UserError(_("Please add fleet tax in %s customer!!!") %
                                rec.customer_id.name)
            analytic_account_ids = rec.customer_id.region_id.analytic_account_id.id
            new_dict = {
                'product_id': product_id,
                'name': 'Charges towards the fleet services b/w %s to %s '
                        '\nTotal no. of trips : %s' % (
                            rec.from_date.strftime('%d/%m/%y'), rec.to_date.strftime('%d/%m/%y'), count),
                'price_unit': rec.grand_total,
                'tax_ids': [(6, 0, rec.customer_id.vehicle_invoice_tax_ids.ids)],
                'analytic_distribution': {analytic_account_ids: 100},
            }
            line_list.append((0, 0, new_dict))
            state_journal = self.env['state.journal'].search(
                [('state_id', '=', rec.customer_id.region_id.state_id.id), ('company_id', '=', rec.company_id.id)])
            if not state_journal.fleet_journal_id:
                raise UserError(
                    _("Please add fleet journal in %s state!!!") % rec.customer_id.region_id.state_id.name)

            vals = {
                'move_type': 'out_invoice',
                'journal_id': state_journal.fleet_journal_id.id,
                'invoice_date': date.today(),
                'partner_id': rec.customer_id.id,
                'state': 'draft',
                'vehicle_ftl_customer_consolidate_id': rec.id,
                'invoice_line_ids': line_list,
                'invoice_origin': rec.name,
                'work_order_ids': [(6, 0, rec.work_order_ids.ids)],
                'work_order_amount': rec.work_order_amount or 0,
                'work_order_shipping_address': rec.work_order_shipping_address or None,
                'company_id': rec.company_id.id,
                'service_type_id': rec.customer_id.service_type_id.id,
                'segment_id': rec.customer_id.segment_id.id,
                'region_id': rec.customer_id.region_id.id if rec.customer_id.region_id else False,
                'sales_person_id': rec.customer_id.order_sales_person.id if rec.customer_id.order_sales_person else False,
            }

            invoices = self.env['account.move'].sudo().create(vals)
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

    def _compute_invoice_count(self):
        """function compute invoice count  to display in smart button"""
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)
            
            
    def action_mail_send_to_partner(self):
        """this function used to send mail to customer about the consolidated trip summary"""
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']

        try:
            compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        except ValueError:
            compose_form_id = False

        batch_trip_report_id = self.env.ref('fleet_ftl.ftl_consolidated_trip_xlsx')
        generated_report = self.env['ir.actions.report']._render_xlsx(batch_trip_report_id,[self.id], data=self.env.context)
        data_record = base64.b64encode(generated_report[0])

        ir_values = {
            'name': 'FTL Trip Summary.xlsx',
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/vnd.ms-excel',
            'res_model': 'trip.summary.ftl',
        }
        attachment = self.env['ir.attachment'].sudo().create(ir_values)
        email_template = self.env.ref('fleet_ftl.consolidated_customer_trip_ftl_send_to_customer_email_template')
        email_template.write({'attachment_ids': [(6, 0, [attachment.id])]})

        ctx = {
            'default_model': 'trip.summary.ftl',
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
            
    def print_xlsx(self):
        """this function used to print xlsx report"""
        for rec in self:
            data = {
                'ids': self.env.context.get('active_ids', []),
                'model': 'trip.summary.ftl',
            }
            report = self.sudo().env.ref('fleet_ftl.ftl_consolidated_trip_xlsx')
            report.report_file = "Customer_Trip_%s_to_%s" % (self.from_date or '', self.to_date or '')
            return report.report_action(self, data=data)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    args.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    args.append(('region_id', 'in', []))
        res = super(FtlTripSummary, self).search(args, offset, limit, order, count=count)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    domain.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    domain.append(('region_id', 'in', []))
        return super(FtlTripSummary, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)


class TripSummaryFtlLines(models.Model):
    _name = 'trip.summary.ftl.line'
    _description = 'Trip Summary FTL Line'

    name = fields.Char(string='Ref. Number')
    work_order_id = fields.Many2one("work.order")
    ftl_batch_trip_id = fields.Many2one(comodel_name='batch.trip.ftl', string="Ftl Daily Trip",
                                        ondelete='cascade', copy=True)
    trip_no = fields.Char(string='Ref. Number')
    trip_summary_ftl_id = fields.Many2one('trip.summary.ftl', ondelete='cascade', index=True, copy=False)
    trip_date = fields.Date(string="Trip Date", store=True)
    customer_id = fields.Many2one('res.partner', string="Customer",
                                  related='trip_summary_ftl_id.customer_id', store=True)
    total_lines_km = fields.Float(string="Total Km")
    total_lines_amount = fields.Float(digits='Product Price', string='Amount')
    # batch_trip_ftl_line_ids = fields.Many2many('batch.trip.ftl.line', copy=False, string='Trip Details')
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        res = super(TripSummaryFtlLines, self).create(vals)
        # adding sequence
        company_id = self.env.company.id
        sequence = self.env['ir.sequence'].search(
            [('company_id', '=', company_id), ('code', '=', 'trip.summary.ftl.line')])
        if not sequence:
            sequence = self.env['ir.sequence'].search([('code', '=', 'trip.summary.ftl.line')], limit=1)
            new_sequence = sequence.sudo().copy()
            new_sequence.company_id = company_id
            res.name = new_sequence.next_by_id()
        else:
            res.name = self.env['ir.sequence'].next_by_code('trip.summary.ftl.line')
        return res

    def unlink(self):
        """extended for resetting the invoice_state and trip_summary_ftl_id of the trip entry on removing from line"""
        for rec in self:
            if rec.ftl_batch_trip_id:
                rec.ftl_batch_trip_id.write({'trip_summary_ftl_id': False, 'invoice_state': 'to_invoice'})
        return super(TripSummaryFtlLines, self).unlink()

    def remove_entry(self):
        """function to remove  entry's trip entry"""
        # rendering  a warning if try to remove all the trip lines
        if len(self.trip_summary_ftl_id.trip_summary_ftl_line_ids) == 1:
            res = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Message',
                    'message': "Cannot create consolidate invoice without "
                               "trip details lines",
                    'sticky': False,
                    'type': 'danger',
                }
            }
            return res
        else:
            charges = {}
            # resetting the additional charges fields on removing line entry's
            if self.trip_summary_ftl_id.deduction > 0:
                charges.update(
                    {'deduction': 0.00, 'deduction_comments': False})
            if self.trip_summary_ftl_id.additional_charge > 0:
                charges.update({'additional_charge': 0.00,
                                'additional_charge_comments': False})
            if charges:
                self.trip_summary_ftl_id.write(charges)
            self.sudo().unlink()
