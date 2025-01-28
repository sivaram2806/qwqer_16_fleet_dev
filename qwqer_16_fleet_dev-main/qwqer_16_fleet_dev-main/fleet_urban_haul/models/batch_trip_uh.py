# -*- coding: utf-8 -*-
import base64

from lxml import etree
from datetime import datetime, timedelta, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import SUPERUSER_ID

from odoo.tools.misc import formatLang

TRIP_STATE = [
    ("new", "New"),
    ("pending_approval", "Pending Approval"),
    ("approved", "Approved"),
    ("completed", "Completed"),
    ("rejected", "Rejected")
]

INVOICE_STATE = [
    ("to_invoice", "To Invoice"),
    ("partial_invoice", "Partially Invoiced"),
    ("invoiced", "Invoiced"),
    ("nothing_to_invoice", "Nothing to Invoice")
]

FREQUENCY = [
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
]

CALCULATION_FREQUENCY = [
    ("daily", "Daily"),
    ("monthly", "Monthly"),
]

BILL_STATE = [
    ("to_paid", "To Be Paid"),
    ("paid", "Billed"),
    ("nothing_to_paid", "Nothing to Bill")
]


class BatchTripUH(models.Model):
    """
    The model used for creating daily urban haul trips
    """
    _name = 'batch.trip.uh'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Batch Trip Urban Haul'
    _order = 'id desc'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(BatchTripUH, self).get_view(view_id=view_id, view_type=view_type, **options)
        doc = etree.XML(res['arch'])

        # Groups Fleet manager and Urban Haul Edit Trip only have the access to edit the trip

        if not self.env.user.has_group('fleet.fleet_group_manager') and not self.env.user.has_group(
                'fleet_urban_haul.group_vehicle_management_enable_edit'):
            if view_type == 'form':
                for node_form in doc.xpath("//form"):
                    node_form.set("edit", 'false')
            if view_type == 'tree':
                for node_form in doc.xpath("//tree"):
                    node_form.set("create", 'false')
                    node_form.set("delete", 'false')

        # Groups Fleet manager and Urban Haul Create/Send for Approval Trip only have the access to create the trip

        if not self.env.user.has_group('fleet.fleet_group_manager') and not self.env.user.has_group(
                'fleet_urban_haul.group_vehicle_management_user'):
            if view_type == 'tree':
                for node_form in doc.xpath("//tree"):
                    node_form.set("create", 'false')
            if view_type == 'form':
                for node_form in doc.xpath("//form"):
                    node_form.set("create", 'false')
        # TODO: commented for using manual vendor trip creation till integrating vendor portal

        #     Daily trip view and vendor daily trip view is separated by passing is_vendor_trip boolean. If it is a
        #     vendor daily trip then create button is removed from the form.
        #     if self.env.context.get('default_is_vendor_trip', False):
        #         if view_type == 'form':
        #             for node_form in doc.xpath("//form"):
        #                 node_form.set("create", 'false')
        #         if view_type == 'tree':
        #             for node_form in doc.xpath("//tree"):
        #                 node_form.set("create", 'false')

        res['arch'] = etree.tostring(doc)
        return res

    # Trip Form
    state = fields.Selection(TRIP_STATE, default=TRIP_STATE[0][0], copy=False, index=True, tracking=True)
    name = fields.Char()
    customer_id = fields.Many2one('res.partner',
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False), ('customer_rank','>', 0)]")
    trip_date = fields.Date()
    invoice_state = fields.Selection(INVOICE_STATE, string='Invoice Status', default=INVOICE_STATE[0][0],
                                     copy=False, index=True, tracking=True,store=True,compute='_compute_invoice_state')
    region_id = fields.Many2one('sales.region', string='Trip Region',
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    frequency = fields.Selection(FREQUENCY, default=FREQUENCY[0][0], string="Frequency", copy=False)
    comments = fields.Text()
    sales_person_id = fields.Many2one('hr.employee', string='Sales Person')
    attachment_ids = fields.Many2many('ir.attachment', 'batch_trip_uh_attachment_rel', 'batch_trip_uh_id',
                                      'attachment_id', string='Attachments')
    filename = fields.Char()

    # Trip Details
    batch_trip_uh_line_ids = fields.One2many('batch.trip.uh.line', 'batch_trip_uh_id', copy=False)

    # Other Info
    mail_approval_received = fields.Selection([
        ("yes", "Yes"),
        ("no", "No")], default="no", string='Mail Approval Received?')
    approved_attachment = fields.Binary(string='Approved Attachment')

    attachment_name = fields.Char(string='Approved Attachment Name')
    approved_user_id = fields.Many2one('res.users', string='Approved User')

    # User Action History
    user_action_ids = fields.One2many('user.action.history', 'batch_trip_uh_id', copy=False)

    # Other fields
    edit_bool = fields.Boolean(string='Edit Bool', compute='_compute_edit_bool', default=True, copy=False)
    is_invoice_paid = fields.Boolean(string='Invoice Paid', compute='_compute_invoice_paid', store=True)
    vendor_total_amount = fields.Float(string='Vendor Total Amount', digits='Product Price',
                                       compute='_compute_total_amount', store=True)
    customer_total_amount = fields.Float(string='Customer Total Amount', digits='Product Price',
                                         compute='_compute_total_amount', store=True)
    # Vendor Daily Trip form view differentiate field
    is_vendor_trip = fields.Boolean(string='Vendor Trip?', default=False, copy=False)

    # Company id for Multi-Company property
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    customer_credit_warning = fields.Text(compute='_check_customer_credit_limit_warning', default=False)
    is_credit_warning_visible = fields.Boolean(readonly=True, default=False, copy=False)

    @api.depends('batch_trip_uh_line_ids.invoice_state')
    def _compute_invoice_state(self):
        """
        Computes the invoice state of the batch trip based on the invoice states
        of its related batch trip lines.
        """
        for trip in self:
            # Collect all unique states from related batch_trip_uh_line_ids
            line_states = set(trip.mapped('batch_trip_uh_line_ids.invoice_state'))

            # Determine batch trip invoice_state based on line states
            if line_states == {"invoiced"}:
                trip.invoice_state = "invoiced"
            elif line_states == {"to_invoice"}:
                trip.invoice_state = "to_invoice"
            elif line_states == {"nothing_to_invoice"}:
                trip.invoice_state = "nothing_to_invoice"
            elif "invoiced" in line_states and "to_invoice" in line_states:
                trip.invoice_state = "partial_invoice"


    def _check_date_constraints(self, trip_date):
        """
        To check the limited back days and raise error not to allow creating trips beyond that date.

            :param trip_date: Trip date of the record.
        """
        back_date = False
        today = date.today()
        limit_days = self.env.company.back_days or '0'
        if limit_days != '0':
            back_days = int(limit_days) - 1
            back_date = today + timedelta(days=-back_days)

        # Raise error if trip date is less than the calculated back date from the days given in the config.
        if back_date and trip_date < back_date:
            raise UserError(_("The No. of back days is set to %s. Creating trips previous to %s are not permitted." %
                              (limit_days, back_date.strftime("%d/%m/%Y"))))
        # Raise error if trip date is greater than today.
        if trip_date > today:
            raise UserError(_("Creating trips ahead of today is not allowed."))

    @api.model
    def create(self, vals):
        """generate sequence for batch trip"""
        company_id = self.env.company.id
        sequence = self.env['ir.sequence'].search(
            [('company_id', '=', company_id), ('code', '=', 'batch.trip.uh')])
        if not sequence:
            sequence = self.env['ir.sequence'].search([('code', '=', 'batch.trip.uh')], limit=1)
            new_sequence = sequence.sudo().sudo().copy()
            new_sequence.company_id = company_id
            vals['name'] = self.env['ir.sequence'].next_by_code('batch.trip.uh')
        else:
            vals['name'] = self.env['ir.sequence'].with_company(company_id).next_by_code('batch.trip.uh')
        res = super(BatchTripUH, self).create(vals)
        for rec in res:
            rec._check_vehicle_pricing_validations()
            self._check_date_constraints(rec.trip_date)
            if vals.get('attachment_ids'):
                rec.attachment_ids.res_id = rec.id
            if not rec.batch_trip_uh_line_ids:
                raise UserError(_("Please add atleast one trip line"))
        return res

    def write(self, vals):
        res = super(BatchTripUH, self).write(vals)
        for rec in self:
            rec._check_vehicle_pricing_validations()
            if 'trip_date' in vals:
                self._check_date_constraints(rec.trip_date)

            if not rec.batch_trip_uh_line_ids:
                raise UserError(_("Please add atleast one trip line"))
        return res

    @api.depends('batch_trip_uh_line_ids.vendor_amount', 'batch_trip_uh_line_ids.customer_amount')
    def _check_customer_credit_limit_warning(self, current_trip_amt=0, stage_change=False):
        for rec in self:
            if  rec.company_id.customer_credit_limit and rec.customer_id.active_limit:
                if rec.batch_trip_uh_line_ids:
                    # (1) customer payable amount
                    invoice_payable = rec.customer_id.credit
                    # (2) total non-invoiced WO amount
                    domain = [('customer_id', '=', rec.customer_id.id),
                             ('state', "not in", ['rejected', 'completed'])]
                    if current_trip_amt:
                        domain.append(('id', "not in", rec.ids))
                    non_invoiced_trips = self.env["batch.trip.uh"].search(domain)
                    non_invoiced_trips_amt = 0.0
                    for item in non_invoiced_trips:
                        for trip in item.batch_trip_uh_line_ids:
                            if not trip.trip_summary_customer_id or not trip.trip_summary_customer_id.invoice_ids.filtered(lambda inv: inv.state == 'posted'):
                                non_invoiced_trips_amt += trip.customer_amount
                    # non_invoiced_trips_amt = sum(non_invoiced_trips.mapped('customer_total_amount'))
                    # (3) current trip amount
                    current_trip_total = current_trip_amt
                    # sum of (1), (2) and (3)
                    total_receivable = invoice_payable + non_invoiced_trips_amt + current_trip_total
                    if total_receivable > rec.customer_id.blocking_stage:
                        raise UserError(
                            _("Customer's existing Trip total payable due has exceeded available credit limit of %s.",
                              (formatLang(rec.env, rec.customer_id.blocking_stage,
                                          currency_obj=rec.company_id.currency_id))))
                    # warning message
                    if (total_receivable / rec.customer_id.blocking_stage) * 100 >= rec.company_id.credit_limit_warning_percent:
                        rec.is_credit_warning_visible = True
                        rec.customer_credit_warning = _(
                            'You have used %s%% of your credit limit of Rs %s',
                            "{:.2f}".format(round((total_receivable / rec.customer_id.blocking_stage) * 100, 2) if rec.customer_id.blocking_stage else 0),
                            formatLang(rec.env, rec.customer_id.blocking_stage, currency_obj=rec.company_id.currency_id))
                    else:
                        rec.is_credit_warning_visible = False
                        rec.customer_credit_warning = False
                else:
                    rec.is_credit_warning_visible = False
                    rec.customer_credit_warning = False
            else:
                rec.is_credit_warning_visible = False
                rec.customer_credit_warning = False

    def unlink(self):
        for rec in self:
            if not self.env.user.has_group('fleet.fleet_group_manager'):
                raise UserError(_("You are not allowed to delete the trip."))
            if rec.state not in ('new', 'rejected'):
                raise UserError(_("You cannot delete the trip when it is not in 'new' or 'rejected' state."))
        return super(BatchTripUH, self).unlink()

    @api.onchange('customer_id')
    def onchange_region(self):
        """
        Onchange customer_id: If Customer is changed then region id,frequency
        and sales person of that customer is set accordingly.
        """
        for rec in self:
            if rec.customer_id:
                rec.region_id = rec.customer_id.region_id.id
                rec.frequency = rec.customer_id.frequency
                rec.sales_person_id = rec.customer_id.order_sales_person.id

    def action_send_for_approve_comment(self):
        """
        Button Send for approval. User action comment wizard is opened when clicked on this and context
        from_send_for_approve is passed as True through this.
        """
        form_view_id = self.env.ref('fleet_urban_haul.user_action_comment_wizard_view_form').id
        for rec in self:
            if rec.state != 'new':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('Trip is in %s state.Please Refresh' % (state)))

            # check customer credit limit
            line_total = sum(rec.batch_trip_uh_line_ids.mapped('customer_amount'))
            self._check_customer_credit_limit_warning(line_total, True)

            ctx = self._context.copy()
            ctx.update({'from_send_for_approve': True})

            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'user.action.comment.wizard',
                'type': 'ir.actions.act_window',
                'view_id': form_view_id
            }

    def action_approve_comment(self):
        """
        Button Approve. This button is in the Pending Approval state.
        """
        for rec in self:
            if rec.state != 'pending_approval':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('Trip is in %s state.Please Refresh' % (state)))
            ctx = self._context.copy()
            ctx.update({'from_approve': True})
            form_view_id = self.env.ref('fleet_urban_haul.user_action_comment_wizard_view_form').id
            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'user.action.comment.wizard',
                'type': 'ir.actions.act_window',
                'view_id': form_view_id
            }

    def action_return_comment(self):
        """
        Button Return. This button is in the Pending Approval state.
        """
        for rec in self:
            if rec.state != 'pending_approval':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('Trip is in %s state.Please Refresh' % (state)))
            ctx = self._context.copy()
            ctx.update({'from_return': True})
            form_view_id = self.env.ref('fleet_urban_haul.user_action_comment_wizard_view_form').id
            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'user.action.comment.wizard',
                'type': 'ir.actions.act_window',
                'view_id': form_view_id
            }

    def action_reject_comment(self):
        """
        Button Reject. This button is in the Pending Approval state.
        """
        for rec in self:
            if rec.state != 'pending_approval':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('Trip is in %s state.Please Refresh' % (state)))
            ctx = self._context.copy()
            ctx.update({'from_reject': True})
            form_view_id = self.env.ref('fleet_urban_haul.user_action_comment_wizard_view_form').id
            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'user.action.comment.wizard',
                'type': 'ir.actions.act_window',
                'view_id': form_view_id
            }

    def action_send_for_approval(self):
        """
        Method used for calculate and compute the customer and vendor amount, raise error if start km is less than end km
        and also if start time is less than end time.
        """
        for rec in self:
            if rec.state != 'new':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('Trip is in %s state.Please Refresh' % (state)))
            ctx = self._context.copy()
            if ctx.get('from_send_for_approve'):
                rec.state = 'pending_approval'

            for line in rec.batch_trip_uh_line_ids:
                if line.end_km < line.start_km:
                    raise UserError(_('End km should be greater start km.'))
                if line.end_time < line.start_time:
                    raise UserError(_('End time should be greater start time.'))

    def action_approved(self):
        for rec in self:
            rec.state = 'approved'

    def calculate_daily_cumulative_amount(self):
        """ Calculate the daily cumulative amount """
        current_date = date.today()
        month_start_date = current_date.replace(day=1)
        self.calculate_cumulative_amount(month_start_date, current_date)

    def calculate_monthly_cumulative_amount(self):
        """ Calculate the monthly cumulative amount """
        current_date = date.today()
        dt = current_date.replace(day=1)
        month_end_date = dt - timedelta(days=1)
        month_start_date = month_end_date.replace(day=1)
        self.calculate_cumulative_amount(month_start_date, month_end_date)

    def calculate_cumulative_amount(self, from_date, to_date):
        """Method for calculating the cumulative amount for both customer and vendor,
        this method is called in the calculation of monthly and daily cumulative amount methods"""
        trip_lines = self.env['batch.trip.uh.line'].search(
            [('trip_date', '>=', from_date), ('trip_date', '<=', to_date),
             '|', ('calculation_frequency', '=', 'monthly'), ('vendor_calculation_frequency', '=', 'monthly'),
             ('batch_trip_uh_id.state', '=', 'approved'), ('batch_trip_uh_id', '!=', False)],
            order='trip_date asc')

        for line in trip_lines:
            self._process_customer_amount(line, from_date, trip_lines)
            self._process_vendor_amount(line, from_date, trip_lines)

    def _process_customer_amount(self, line, from_date, all_lines):
        """Calculate the cumulative customer amount """
        if line.calculation_frequency == 'monthly' and line.customer_id.partner_vehicle_pricing_ids:
            customer_pricing_id = self.env['partner.vehicle.pricing'].search(
                [('partner_id', '=', line.customer_id.id),
                 ('vehicle_pricing_id', '=', line.vehicle_pricing_id.id)], limit=1)
            filtered_lines = all_lines.filtered(lambda trip_uh_line: trip_uh_line.vehicle_pricing_id == line.vehicle_pricing_id and
                                                                     trip_uh_line.customer_id == line.customer_id and
                                                                     from_date <= trip_uh_line.trip_date <= line.batch_trip_uh_id.trip_date and
                                                                     trip_uh_line.region_id == line.region_id)
            if customer_pricing_id and filtered_lines:
                line.cumulative_customer_amount = self._compute_monthly_amount(customer_pricing_id,
                                                                                   filtered_lines)

    def _process_vendor_amount(self, line, from_date, all_lines):
        """Calculate the cumulative vendor amount """
        if line.vendor_calculation_frequency == 'monthly' and line.vendor_id.partner_vehicle_pricing_ids:
            vendor_pricing_id = self.env['partner.vehicle.pricing'].search(
                [('partner_id', '=', line.vendor_id.id),
                 ('vehicle_pricing_id', '=', line.vehicle_pricing_id.id)], limit=1)
            filtered_lines = all_lines.filtered(lambda trip_uh_line: trip_uh_line.vehicle_pricing_id == line.vehicle_pricing_id and
                                                                     trip_uh_line.vendor_id == line.vendor_id and
                                                                     from_date <= trip_uh_line.trip_date <= line.batch_trip_uh_id.trip_date and
                                                                     trip_uh_line.region_id == line.region_id)
            if vendor_pricing_id and filtered_lines:
                line.cumulative_vendor_amount = self._compute_monthly_amount(vendor_pricing_id,
                                                                                   filtered_lines)

    def _compute_monthly_amount(self, pricing_id, trips):
        total_time = sum(trips.mapped('total_time')) or 0.0
        total_km = sum(trips.mapped('total_km')) or 0.0
        km_cost = 0.0
        hour_cost = 0.0
        if total_km:
            if total_km <= pricing_id.base_dist:
                km_cost = (pricing_id.base_cost) or 0.0
            else:
                km_cost = (((total_km - pricing_id.base_dist) * pricing_id.charge_per_km) + pricing_id.base_cost) or 0.0
        if total_time:
            if total_time <= pricing_id.base_hrs:
                hour_cost = (pricing_id.base_cost_hrs) or 0.0
            else:
                hour_cost = (((total_time - pricing_id.base_hrs) * pricing_id.additional_hrs)
                             + pricing_id.base_cost_hrs) or 0.0
        amount = (km_cost + hour_cost) or 0.0
        return amount

    def action_return(self):
        """
        Return Button
        """
        for rec in self:
            rec.state = 'new'

    def action_rejected(self):
        """
        Reject Button
        """
        for rec in self:
            for line in rec.batch_trip_uh_line_ids:
                line.customer_amount = 0
                line.vendor_amount = 0
            rec.state = 'rejected'
            rec.invoice_state = 'nothing_to_invoice'
            rec.batch_trip_uh_line_ids.write({'bill_state': 'nothing_to_paid',
                                              'invoice_state': 'nothing_to_invoice'})

    def action_send_to_customer(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']


        try:
            compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        except ValueError:
            compose_form_id = False

        batch_trip_report_id = self.env.ref('fleet_urban_haul.batch_trip_report_xlsx')
        generated_report = self.env['ir.actions.report'].sudo()._render_xlsx(batch_trip_report_id,[self.id], data=self.env.context)
        data_record = base64.b64encode(generated_report[0])

        ir_values = {
            'name': 'Batch Trip.xlsx',
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/vnd.ms-excel',
            'res_model': 'batch.trip.uh',
        }
        attachment = self.env['ir.attachment'].sudo().create(ir_values)
        email_template = self.env.ref('fleet_urban_haul.batch_trip_send_to_customer_email_template')
        email_template.write({'attachment_ids': [(6, 0, [attachment.id])]})

        ctx = {
            'default_model': 'batch.trip.uh',
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

    def get_submit_email_to(self):
        mail = []
        joined_string = ""
        approval_users = self.env.ref('fleet_urban_haul.group_vehicle_management_approver')
        approval_group = self.env.ref('fleet_urban_haul.group_notify_urban_haul_trip_approver')
        if approval_users and approval_group:
            for user in approval_group.users:
                mail.append(user.partner_id.email or '')
        if mail:
            joined_string = ",".join(mail)
        return joined_string

    def _compute_edit_bool(self):
        """
        Edit bool is used for giving edit access to specific fields for specific groups
        """
        for rec in self:
            rec.edit_bool = True
            if rec.state == 'new':
                if self.env.user.has_group('fleet_urban_haul.group_vehicle_management_user') or self.env.user.has_group(
                        'fleet.fleet_group_manager'):
                    rec.edit_bool = True
                else:
                    rec.edit_bool = False
            elif rec.state == 'pending_approval':
                if (self.env.user.has_group('fleet_urban_haul.group_vehicle_management_approver') or
                        self.env.user.has_group('fleet.fleet_group_manager')):
                    rec.edit_bool = True
                else:
                    rec.edit_bool = False
            elif rec.state == 'approved' or rec.state == 'completed' or rec.state == 'rejected':
                rec.edit_bool = False

    @api.depends('batch_trip_uh_line_ids.vendor_amount', 'batch_trip_uh_line_ids.customer_amount')
    def _compute_total_amount(self):
        """
        Compute Vendor amount and Customer amount
        """
        for rec in self:
            vendor_total_amount = sum(rec.batch_trip_uh_line_ids.mapped('vendor_amount'))
            customer_total_amount = sum(rec.batch_trip_uh_line_ids.mapped('customer_amount'))
            rec._check_customer_credit_limit_warning(customer_total_amount)
            rec.vendor_total_amount = vendor_total_amount
            rec.customer_total_amount = customer_total_amount


    @api.depends('batch_trip_uh_line_ids.trip_summary_customer_id.state',
                 'batch_trip_uh_line_ids.trip_summary_vendor_id.state')
    def _compute_invoice_paid(self):
        """
        Compute whether customer invoice and vendor bill is paid
        """
        for rec in self:
            rec.is_invoice_paid = False
            if rec.batch_trip_uh_line_ids:
                batch_trip_uh_line = rec.batch_trip_uh_line_ids.filtered(
                    lambda
                        s: s.trip_summary_customer_id.state != 'paid' or s.trip_summary_vendor_id.state != 'paid')
                if batch_trip_uh_line:
                    rec.is_invoice_paid = False
                else:
                    rec.is_invoice_paid = True
                    rec.state = 'completed'
            else:
                rec.is_invoice_paid = False

    def _check_vehicle_pricing_validations(self):
        vehicle_no = []
        multiple_vehicle_no = []
        customer_pricing = []
        customer_pricing_name = []
        vendor_pricing = []
        vendor_pricing_names = []
        vendor = []
        vendor_names = []
        vehicle_pricing = []

        for line in self.batch_trip_uh_line_ids:
            v_no = line.vehicle_pricing_line_id.vehicle_no.vehicle_no
            if v_no not in vehicle_no:
                vehicle_no.append(v_no)
                if line.vehicle_pricing_id:
                    cust_vehicle_pricing = line.customer_id.partner_vehicle_pricing_ids.filtered(
                        lambda s: s.vehicle_pricing_id == line.vehicle_pricing_id)
                    if not cust_vehicle_pricing and line.vehicle_pricing_id.id not in customer_pricing:
                        customer_pricing.append(line.vehicle_pricing_id.id)
                        customer_pricing_name.append(line.vehicle_pricing_id.name)

                    vend_vehicle_pricing = line.vendor_id.partner_vehicle_pricing_ids.filtered(
                        lambda s: s.vehicle_pricing_id == line.vehicle_pricing_id)
                    if not vend_vehicle_pricing:
                        if line.vehicle_pricing_id.id not in vendor_pricing:
                            vendor_pricing.append(line.vehicle_pricing_id.id)
                            vendor_pricing_names.append(line.vehicle_pricing_id.name)
                        if line.vendor_id.id not in vendor:
                            vendor.append(line.vendor_id.id)
                            vendor_names.append(line.vendor_id.name)
                else:
                    vehicle_pricing.append(v_no)
            else:
                multiple_vehicle_no.append(v_no)

        is_internal_user = self.env.user.has_group('base.group_user')

        if multiple_vehicle_no:
            raise UserError(_(
                f"Below vehicle no{' is' if len(multiple_vehicle_no) == 1 else 's are'} selected multiple times \n" + "\n".join(
                    multiple_vehicle_no)
            ))

        if vehicle_pricing:
            if not is_internal_user:
                msg = f"vehicle pricing in following vehicle is not configured{'s' if len(vehicle_pricing) > 1 else ''}\n" + "\n".join(
                    vehicle_pricing) + " Please contact the admin"
            else:
                msg = f"Please configure vehicle pricing in below vehicle{'s' if len(vehicle_pricing) > 1 else ''}\n" + "\n".join(
                    vehicle_pricing)
            raise UserError(_(msg))

        if customer_pricing:
            if not is_internal_user:
                msg = (f"vehicle pricing {', '.join(customer_pricing_name)} is not configured for the customer Please "
                       f"contact the admin")
            else:
                msg = f"Please configure vehicle pricing {', '.join(customer_pricing_name)} in customer master"
            raise UserError(_(msg))

        if vendor_pricing:
            if not is_internal_user:
                msg = (
                        f"vehicle pricing {', '.join(vendor_pricing_names)} is not configured for "
                        f"{'s' if len(vendor) > 1 else ''}\n" +
                        "\n".join(vendor_names) +
                        " please contact the admin"
                )
            else:
                msg = f"Please configure vehicle pricing {', '.join(vendor_pricing_names)} in below vendor{'s' if len(vendor) > 1 else ''}\n" + "\n".join(
                    vendor_names)
            raise UserError(_(msg))

    def print_xlsx(self):
        for rec in self:
            data = {
                'ids': self.env.context.get('active_ids', []),
                'model': 'batch.trip',
            }
            report = self.sudo().env.ref('fleet_urban_haul.batch_trip_report_xlsx')
            report.report_file = "Trip_%s" % (self.trip_date or '')
            return report.report_action(self, data=data)

    def created_user_email(self):
        """Used to get the mail id of the partner related to the user logged in"""
        for rec in self:
            mail = rec.create_uid.partner_id.email
            return mail

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # if self.env.user.id != SUPERUSER_ID:
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    args.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    args.append(('region_id', 'in', []))
        res = super(BatchTripUH, self).search(args, offset, limit, order, count=count)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    domain.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    domain.append(('region_id', 'in', []))
        return super(BatchTripUH, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)
    
    
    def get_company_wise(self,company,trip_list,total_revenue,total_cost):
        total_margin = (total_revenue - total_cost) or 0.0
        total_margin_percentage = 0.0
        if total_revenue > 0.0:
            total_margin_percentage = ((total_margin/total_revenue) * 100) or 0.0
        grand_total = {
                    'total_revenue':total_revenue,
                    'total_cost':total_cost,
                    'total_margin':total_margin,
                    'total_margin_percentage':total_margin_percentage,
                    }
        company_wise = {
                'company_name':company.display_name,
                'data':trip_list,
                'total':grand_total}
        return company_wise
    
    def get_revenue_cost(self,trips,customer=True):
        """
        Calculate revenue and cost
        """
        revenue = 0
        cost = 0
        if customer:
            daily_wise_trip = trips.filtered(lambda s: s.calculation_frequency == 'daily')
            if daily_wise_trip:
                revenue += sum(daily_wise_trip.mapped('customer_amount')) or 0.0
            monthly_wise_trip = trips.filtered(lambda s: s.calculation_frequency == 'monthly')
        else:
            daily_wise_trip = trips.filtered(lambda s: s.vendor_calculation_frequency == 'daily')
            if daily_wise_trip:
                cost += sum(daily_wise_trip.mapped('vendor_amount')) or 0.0
            monthly_wise_trip = trips.filtered(lambda s: s.vendor_calculation_frequency == 'monthly')
        
        if monthly_wise_trip:
            vehicles = monthly_wise_trip.mapped('vehicle_pricing_line_id')
            for vehicle in vehicles:
                vehicle_lines = monthly_wise_trip.filtered(lambda s: s.vehicle_pricing_line_id.id == vehicle.id)
                if vehicle_lines:
                    if customer:
                        revenue += max(vehicle_lines.mapped('cumulative_customer_amount')) or 0.0
                    else:
                        cost += max(vehicle_lines.mapped('cumulative_vendor_amount')) or 0.0
        return [revenue,cost]
    
    
    def action_get_customer_wise_data(self,start_date,end_date):
        """
        Get customer wise data
        """
        daily_trips = self.env['batch.trip.uh.line'].search([('batch_trip_uh_id.state', 'in', ('approved','completed')),
                                                          ('trip_date', '>=', start_date), ('trip_date', '<=', end_date)])
        company_wise_trip_list = []
        if daily_trips:
            companies = daily_trips.mapped('company_id')
            for company in companies:
                customer_wise_trip_list = []
                total_revenue = 0.0
                total_cost = 0.0
                company_wise_trip = daily_trips.filtered(lambda s: s.company_id == company)
                customers = company_wise_trip.mapped('customer_id')
                for customer in customers:
                    customer_wise_trip = company_wise_trip.filtered(lambda s: s.customer_id == customer)
                    if customer_wise_trip:
                        revenue = self.get_revenue_cost(customer_wise_trip, True)[0]
                        cost = self.get_revenue_cost(customer_wise_trip, False)[1]
                        margin = (revenue - cost) or 0.0
                        margin_percentage = 0.0
                        if revenue > 0.0:
                            margin_percentage = ((margin  / revenue) * 100) or 0.0
                        vals = {
                            'customer':customer.name,
                            'region':customer.region_id.name,
                            'revenue':revenue,
                            'cost':cost,
                            'margin':margin,
                            'margin_percentage': margin_percentage,
                        }
                        customer_wise_trip_list.append(vals)
                        total_revenue += revenue or 0.0
                        total_cost += cost or 0.0
                if customer_wise_trip_list:  
                    company_wise_trip_list.append(self.get_company_wise(company,customer_wise_trip_list,total_revenue,total_cost))
                
        return company_wise_trip_list
    
    def action_get_region_wise_data(self,start_date,end_date):
        """
        Get region wise data
        """
        daily_trips = self.env['batch.trip.uh.line'].search([('batch_trip_uh_id.state', 'in', ('approved','completed')),
                                                          ('trip_date', '>=', start_date), ('trip_date', '<=', end_date)])
        company_wise_trip_list = []
        if daily_trips:
            companies = daily_trips.mapped('company_id')
            for company in companies:
                region_wise_trip_list = []
                total_revenue = 0.0
                total_cost = 0.0
                company_wise_trip = daily_trips.filtered(lambda s: s.company_id == company)
                region_ids = company_wise_trip.mapped('region_id')
                for region in region_ids:
                    region_wise_trip = company_wise_trip.filtered(lambda s: s.region_id == region)
                    if region_wise_trip:
                        revenue = self.get_revenue_cost(region_wise_trip, True)[0]
                        cost = self.get_revenue_cost(region_wise_trip, False)[1]
                        margin = (revenue - cost) or 0.0
                        margin_percentage = 0.0
                        if revenue > 0.0:
                            margin_percentage = ((margin  / revenue)* 100) or 0.0
                        vals = {
                            'region':region.name,
                            'revenue':revenue,
                            'cost':cost,
                            'margin':margin,
                            'margin_percentage': margin_percentage,
                        }
                        region_wise_trip_list.append(vals)
                        total_revenue += revenue or 0.0
                        total_cost += cost or 0.0
                if region_wise_trip_list:
                    company_wise_trip_list.append(self.get_company_wise(company,region_wise_trip_list,total_revenue,total_cost))
        
        return company_wise_trip_list
    
    def action_send_revenue_report(self,month=False):
        """
        Cron function: for sending daily/monthly revenue report
        """
        if month:
            template = self.env.ref('fleet_urban_haul.mail_template_uh_monthly_revenue_report')
        else:
            template = self.env.ref('fleet_urban_haul.mail_template_uh_daily_revenue_report')
        if template:
            users = self.env.ref('fleet_urban_haul.group_send_uh_revenue_report').users
            res = self.env['res.users'].search_read([('id', 'in', users.ids)], ['email'])
            emails = set(r['email'] for r in res if r.get('email'))
            if month:
                dt = date.today().replace(day=1)
                end_date = dt - timedelta(days=1)
            else:
                end_date = date.today() + timedelta(days=-1)
            start_date = end_date.replace(day=1)
            email_values={
                    'start_date': start_date.strftime("%d-%m-%Y"),
                    'end_date': end_date.strftime("%d-%m-%Y"),
                    'month': start_date.strftime("%b %Y"),
                    'revenue_for_customer':self.action_get_customer_wise_data(start_date,end_date),
                    'revenue_for_region':self.action_get_region_wise_data(start_date,end_date),
                    }
            template.with_context(email_values).send_mail(self.id, email_values={'email_to': ','.join(emails)}, force_send = True)
            
    
class BatchTripUHLine(models.Model):
    """
    Batch Trip Line class for Urban Haul. This model stores the lines of urban haul batch trips.
    This model is related to the above model batch.trip.
    """
    _name = 'batch.trip.uh.line'
    _description = 'Batch Trip UH Line'

    trip_no = fields.Char()
    vehicle_pricing_line_id = fields.Many2one('vehicle.pricing.line')
    vehicle_model_id = fields.Many2one('fleet.vehicle.model',
                                       related='vehicle_pricing_line_id.vehicle_no.vehicle_model_id')
    vehicle_pricing_id = fields.Many2one('vehicle.pricing', string='Vehicle Pricing', store=True)
    vehicle_description = fields.Char(string='Vehicle Description',
                                      related='vehicle_pricing_line_id.vehicle_description')
    vendor_id = fields.Many2one('res.partner',
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False), ('supplier_rank', '>', 0)]")
    bill_state = fields.Selection(BILL_STATE, string='Bill Status', default=BILL_STATE[0][0], copy=False, index=True)
    invoice_state = fields.Selection(INVOICE_STATE, string='Invoice Status', default=INVOICE_STATE[0][0], copy=False, index=True)
    start_time = fields.Float(default=9.0)
    end_time = fields.Float(default=18.0)
    total_time = fields.Float(compute='_compute_total_time', store=True)
    start_km = fields.Float(string="Start Odo")
    end_km = fields.Float(string="End Odo")
    total_km = fields.Float(string="Total Odo", compute='_compute_total_km', store=True)
    customer_km_cost = fields.Float(digits='Product Price')
    customer_hour_cost = fields.Float(digits='Product Price')
    vendor_km_cost = fields.Float(digits='Product Price')
    vendor_hour_cost = fields.Float(digits='Product Price')
    customer_amount = fields.Float(digits='Product Price', compute='_compute_calculation_frequency', store=True)
    vendor_amount = fields.Float(digits='Product Price', compute='_compute_calculation_frequency', store=True)
    customer_id = fields.Many2one('res.partner', related='batch_trip_uh_id.customer_id', store=True, index=True)
    region_id = fields.Many2one('sales.region', string='Trip Region', related='batch_trip_uh_id.region_id', store=True,
                                index=True)
    frequency = fields.Selection(FREQUENCY, default=FREQUENCY[0][0], string="Customer Invoice Frequency",
                                 related='batch_trip_uh_id.frequency', store=True, index=True)
    calculation_frequency = fields.Selection(CALCULATION_FREQUENCY, default=CALCULATION_FREQUENCY[0][0],
                                             string="Customer Calculation Method",
                                             compute='_compute_calculation_frequency',
                                             copy=False, store=True)

    vendor_calculation_frequency = fields.Selection(CALCULATION_FREQUENCY, default=CALCULATION_FREQUENCY[0][0],
                                                    string=" Vendor Calculation Method",
                                                    compute='_compute_calculation_frequency',
                                                    copy=False, store=True)
    driver_name = fields.Char()
    trip_date = fields.Date(related='batch_trip_uh_id.trip_date', store=True, index=True)
    cumulative_vendor_amount = fields.Float(digits='Product Price', string='Cumulative Vendor Amount')
    cumulative_customer_amount = fields.Float(digits='Product Price', string='Cumulative Customer Amount')
    batch_trip_uh_id = fields.Many2one('batch.trip.uh', string="Daily Trip", ondelete='cascade', index=True, copy=True)
    trip_summary_customer_id = fields.Many2one('trip.summary.uh', string='Trip Summary Customer', index=True)
    trip_summary_vendor_id = fields.Many2one('trip.summary.uh', string='Trip Summary Vendor', index=True)
    # Company id for Multi-Company property
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        """generate sequence for batch trip line"""
        company_id = self.env.company.id
        sequence = self.env['ir.sequence'].search(
            [('company_id', '=', company_id), ('code', '=', 'batch.trip.uh.line')])
        if not sequence:
            sequence = self.env['ir.sequence'].search([('code', '=', 'batch.trip.uh.line')], limit=1)
            new_sequence = sequence.sudo().copy()
            new_sequence.company_id = company_id
            vals['trip_no'] = new_sequence.next_by_id()
        else:
            vals['trip_no'] = self.env['ir.sequence'].with_company(company_id).next_by_code('batch.trip.uh.line')
        res = super(BatchTripUHLine, self).create(vals)
        # raise error if state is in approved and try to create new trip lines
        if res.batch_trip_uh_id.state == 'approved':
            raise UserError(_('Adding trip lines is restricted in approved state!!!'))
        for rec in res:
            daily_trips = self.env['batch.trip.uh.line'].search(
                [('batch_trip_uh_id', '!=', rec.batch_trip_uh_id.id), ('batch_trip_uh_id', '!=', False),
                 ('batch_trip_uh_id.state', '!=', 'rejected'),
                 ('vehicle_pricing_line_id', '=', rec.vehicle_pricing_line_id.id),
                 ('batch_trip_uh_id.trip_date', '=', rec.trip_date),
                 '|', ('start_time', '<', rec.start_time), ('start_time', '<', rec.end_time),
                 '|', ('end_time', '>', rec.start_time), ('end_time', '>', rec.end_time)], limit=1)
            # raise error if trip is already exist in the same date.
            if daily_trips:
                trip_date = rec.trip_date.strftime("%d-%m-%Y")
                is_internal_user = self.env.user.has_group('base.group_user')
                msg = (f"Daily trip {daily_trips.batch_trip_uh_id.name} has been created within this time period with "
                       f"trip date {trip_date}.")
                if is_internal_user:
                    msg = msg + f"\nPlease contact {daily_trips.create_uid.name}"
                raise UserError(_(msg))
        return res

    def write(self, vals):
        res = super(BatchTripUHLine, self).write(vals)
        for rec in self:
            if 'start_time' in vals or 'end_time' in vals:
                daily_trips = self.env['batch.trip.uh.line'].search(
                    [('batch_trip_uh_id', '!=', rec.batch_trip_uh_id.id), ('batch_trip_uh_id', '!=', False),
                     ('batch_trip_uh_id.state', '!=', 'rejected'),
                     ('vehicle_pricing_line_id', '=', rec.vehicle_pricing_line_id.id),
                     ('batch_trip_uh_id.trip_date', '=', rec.trip_date),
                     '|', ('start_time', '<', rec.start_time), ('start_time', '<', rec.end_time),
                     '|', ('end_time', '>', rec.start_time), ('end_time', '>', rec.end_time)], limit=1)
                # raise error if trip is already exist in the same date.
                if daily_trips:
                    trip_date = rec.trip_date.strftime("%d-%m-%Y")
                    raise UserError(
                        _(f"Daily trip {daily_trips.batch_trip_uh_id.name} has been created within this time period "
                          f"with trip date {trip_date}.\nPlease contact {daily_trips.create_uid.name}"))
        return res

    @api.onchange('vehicle_pricing_line_id')
    def onchange_vendor(self):
        """
        Onchange vehicle_pricing_line_id: Set vendor_id, driver_name, and vehicle_pricing_id based on selected vehicle number.
        """
        for rec in self:
            if rec.vehicle_pricing_line_id:
                rec.vendor_id = rec.vehicle_pricing_line_id.vendor_id.id
                rec.driver_name = rec.vehicle_pricing_line_id.driver_name
                rec.vehicle_pricing_id = rec.vehicle_pricing_line_id.vehicle_pricing_id.id

    def calculate_customer_amount(self, line):
        """
        Function for calculation customer amount from the vehicle pricing given for the specific
        customer in res.partner.
        """
        customer_vehicle_id = self.customer_id.partner_vehicle_pricing_ids.filtered(
                    lambda s: s.vehicle_pricing_id.id == line.vehicle_pricing_id.id)
        customer_vehicle_id = customer_vehicle_id and customer_vehicle_id[0]
        if customer_vehicle_id and line.calculation_frequency == 'daily':
            if line.total_km:
                if line.total_km <= customer_vehicle_id.base_dist:
                    line.customer_km_cost = customer_vehicle_id.base_cost
                else:
                    line.customer_km_cost = ((line.total_km - customer_vehicle_id.base_dist) * customer_vehicle_id.charge_per_km) + customer_vehicle_id.base_cost
            else:
                line.customer_km_cost = 0.0
            if line.total_time:
                if line.total_time <= customer_vehicle_id.base_hrs:
                    line.customer_hour_cost = customer_vehicle_id.base_cost_hrs
                else:
                    line.customer_hour_cost = ((line.total_time - customer_vehicle_id.base_hrs) * customer_vehicle_id.additional_hrs) + customer_vehicle_id.base_cost_hrs
            else:
                line.customer_hour_cost = 0.0
            line.customer_amount = line.customer_km_cost + line.customer_hour_cost
        else:
            line.customer_amount = 0

    def calculate_vendor_amount(self, line):
        """
        Function for calculation vendor amount from the vehicle pricing given for the specific
        vendor in res.partner.
        """
        vendor_vehicle_id = self.vendor_id.partner_vehicle_pricing_ids.filtered(
                    lambda s: s.vehicle_pricing_id.id == line.vehicle_pricing_id.id)
        vendor_vehicle_id = vendor_vehicle_id and vendor_vehicle_id[0]
        if vendor_vehicle_id and line.vendor_calculation_frequency == 'daily':
            if line.total_km:
                if line.total_km <= vendor_vehicle_id.base_dist:
                    line.vendor_km_cost = vendor_vehicle_id.base_cost
                else:
                    line.vendor_km_cost = ((line.total_km - vendor_vehicle_id.base_dist) * vendor_vehicle_id.charge_per_km) + vendor_vehicle_id.base_cost
            else:
                line.vendor_km_cost = 0.0
            if line.total_time:
                if line.total_time <= vendor_vehicle_id.base_hrs:
                    line.vendor_hour_cost = vendor_vehicle_id.base_cost_hrs
                else:
                    line.vendor_hour_cost = ((line.total_time - vendor_vehicle_id.base_hrs) * vendor_vehicle_id.additional_hrs) + vendor_vehicle_id.base_cost_hrs
            else:
                line.vendor_hour_cost = 0.0
            line.vendor_amount = line.vendor_km_cost + line.vendor_hour_cost
        else:
            line.vendor_amount = 0

    @api.depends('vehicle_pricing_id', 'start_km', 'end_km', 'start_time', 'end_time', 'vehicle_pricing_line_id',
                 'vehicle_pricing_id')
    def _compute_calculation_frequency(self):
        """Compute and calculate invoice frequency and vendor frequency.
           To compute customer amount and vendor amount for daily vehicle pricing."""
        for rec in self:
            rec.calculation_frequency = False
            rec.vendor_calculation_frequency = False
            if rec.customer_id.partner_vehicle_pricing_ids:
                vehicle_lines = rec.customer_id.partner_vehicle_pricing_ids.filtered(
                    lambda s: s.vehicle_pricing_id.id == rec.vehicle_pricing_id.id)
                rec.calculation_frequency = vehicle_lines and vehicle_lines[0].trip_frequency or ""
            if rec.vendor_id.partner_vehicle_pricing_ids:
                vehicle_lines = rec.vendor_id.partner_vehicle_pricing_ids.filtered(
                    lambda s: s.vehicle_pricing_id.id == rec.vehicle_pricing_id.id)
                rec.vendor_calculation_frequency = vehicle_lines and vehicle_lines[0].trip_frequency or ""
            if rec.customer_id.partner_vehicle_pricing_ids:
                rec.calculate_customer_amount(rec)
            if rec.vendor_id.partner_vehicle_pricing_ids:
                rec.calculate_vendor_amount(rec)

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

    @api.onchange('invoice_state')
    def _onchange_invoice_state(self):
        if self.batch_trip_uh_id:
            self.batch_trip_uh_id._compute_invoice_state()
