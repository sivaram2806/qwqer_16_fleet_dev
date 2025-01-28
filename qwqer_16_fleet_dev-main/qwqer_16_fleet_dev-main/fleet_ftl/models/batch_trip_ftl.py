# -*- coding: utf-8 -*-
import base64

from lxml import etree
from odoo import fields, models, api, _
from datetime import timedelta, date
from odoo.exceptions import UserError
from odoo import SUPERUSER_ID


class BatchTripFTLLine(models.Model):
    """
    Model contains records from batch trip line, #V13_model name: ftl.batch.trip.line
    """
    _name = 'batch.trip.ftl.line'
    _description = 'Batch Trip FTL Line'

    trip_no = fields.Char(string='Trip Number')
    ftl_batch_trip_id = fields.Many2one(comodel_name='batch.trip.ftl', string="Ftl Daily Trip",
                                        ondelete='cascade', copy=True)
    vehicle_id = fields.Many2one(string='Vehicle Number', comodel_name='vehicle.vehicle')
    vehicle_model_id = fields.Many2one(string='Vehicle Model', comodel_name='fleet.vehicle.model',
                                       related='vehicle_id.vehicle_model_id', store=True)
    vehicle_type_id = fields.Many2one(string='Vehicle Type', related='vehicle_id.vehicle_type_id', store=True)
    vehicle_description = fields.Char(string='Vehicle Description')
    package_description = fields.Char(string='Package Description')
    start_date = fields.Date(string='Start date', required=True)
    end_date = fields.Date(string='End date', required=True)
    total_km = fields.Float(string='Total KM')
    quantity = fields.Integer(string='Qty', default=1)
    tonnage = fields.Integer(string='Tonnage', default=1)
    amount = fields.Monetary(string='Amount')
    company_id = fields.Many2one(comodel_name='res.company', string="Company", required=True, readonly=True,
                                 default=lambda self: self.env.company)
    source_id = fields.Many2one("res.state.city")
    destination_id = fields.Many2one("res.state.city")
    work_order_id = fields.Many2one(comodel_name='work.order', string='Work Order',
                                    related='ftl_batch_trip_id.work_order_id', store=True)
    currency_id = fields.Many2one(comodel_name='res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id)
    total_amount = fields.Monetary(string='Total Customer Price', related="ftl_batch_trip_id.total_amount",
                                   store=True)
    vendor_cost = fields.Monetary(string='Total Vendor Cost', related="ftl_batch_trip_id.vendor_cost",
                                  store=True)

    @api.model
    def create(self, vals):
        """Inheriting default create function to generate trip number for trip line"""
        company_id = self.env.company.id
        sequence = self.env['ir.sequence'].search(
            [('company_id', '=', company_id), ('code', '=', 'fleet.ftl.dt.line.seq')])
        if not sequence:
            sequence = self.env['ir.sequence'].search([('code', '=', 'fleet.ftl.dt.line.seq')], limit=1)
            new_sequence = sequence.sudo().copy()
            new_sequence.company_id = company_id
            code = new_sequence.next_by_id()
        else:
            code = self.env['ir.sequence'].next_by_code('fleet.ftl.dt.line.seq')
        vals['trip_no'] = code
        res = super().create(vals)
        if res.ftl_batch_trip_id.state == 'approved':
            raise UserError(_('Adding trip lines is restricted in approved state!!!'))
        return res

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.ftl_batch_trip_id.trip_date and self.start_date:
            if self.start_date < self.ftl_batch_trip_id.trip_date:
                raise UserError(_('Start date should be after or equal to Trip Date'))
        if self.end_date:
            if not self.start_date or self.start_date > self.end_date:
                raise UserError(_('Start date should be before or equal to End Date'))

    @api.onchange('end_date')
    def _onchange_send_date(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise UserError(_('End date should be after or equal to Start Date'))
        if self.ftl_batch_trip_id.trip_date and self.end_date:
            if self.end_date < self.ftl_batch_trip_id.trip_date:
                raise UserError(_('End date should be after or equal to Trip Date'))

    def default_get(self, fields):
        """overridden default_get to update start date, end date and tonnage default values"""
        res = super(BatchTripFTLLine, self).default_get(fields)
        if self.env.context.get("work_order_id"):
            work_order = self.env["work.order"].browse(self.env.context.get("work_order_id"))
            if not res.get('start_date'):
                res["start_date"] = work_order.delivery_date_from
            if not res.get("end_date"):
                res["end_date"] = work_order.delivery_date_to
            if work_order and work_order.work_order_line_ids:
                res['tonnage'] = work_order.work_order_line_ids[0].tonnage
        return res


class BatchTripFTL(models.Model):
    """
    Model contains records from batch trip, #V13_model name: batch.trip
    """
    _name = 'batch.trip.ftl'
    _description = "Batch Trip FTL"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Trip Number')
    trip_date = fields.Date(string='Trip Date')
    customer_id = fields.Many2one(comodel_name='res.partner', string='Customer',
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor',
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    region_id = fields.Many2one(comodel_name='sales.region', string='Region',
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    comments = fields.Text()
    invoice_state = fields.Selection([
        ("to_invoice", "To Invoice"),
        ("invoiced", "Invoiced"),
        ("nothing_to_invoice", "Nothing to Invoice")], string='Invoice Status',
        default="to_invoice", copy=False, index=True, tracking=True)
    state = fields.Selection([
        ("new", "New"),
        ("pending_approval", "Pending Approval"),
        ("ops_approved", "Ops Approved"),
        ("finance_approved", "Finance Approved"),
        ("completed", "Completed"),
        ("rejected", "Rejected")], default="new", copy=False, tracking=True)
    batch_trip_line_ids = fields.One2many(comodel_name='batch.trip.ftl.line', inverse_name='ftl_batch_trip_id',
                                          copy=False)
    user_action_ids = fields.One2many(comodel_name='ftl.user.action.history', inverse_name='batch_trip_ftl_id',
                                      copy=False)
    is_editable = fields.Boolean(string='Edit Bool', compute='_compute_is_editable', default=True, copy=False)
    is_invoice_paid = fields.Boolean(string='Invoice Paid')
    trip_type = fields.Selection([('fleet_urban_haul', 'Fleet Urban Haul'), ('fleet_ftl', 'Fleet FTL')])
    work_order_id = fields.Many2one(comodel_name='work.order', string='Work Order')
    currency_id = fields.Many2one(comodel_name='res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id)
    work_order_amount = fields.Monetary(string='Work Order Amount', related='work_order_id.total_amount', store=True)
    work_order_shipping_address = fields.Text(string='Work Order Shipping Address',
                                              related='work_order_id.shipping_address', store=True)
    lorry_receipt_no = fields.Char(string='Lorry Receipt No')
    ftl_multi_attachment_ids = fields.Many2many(comodel_name='ir.attachment', inverse_name='ftl_attachment_id',
                                                string="Attachments")
    pod_attachment = fields.Binary(string="POD Attachment")
    pod_attachment_name = fields.Char(string="POD Attachment Name")
    eway_bill_number = fields.Char(string='Eway Bill Number')
    total_trip_amount = fields.Monetary(string='Total Trip Amount', store=True)
    trip_summary_ftl_id = fields.Many2one(comodel_name='trip.summary.ftl', ondelete='cascade', index=True, copy=False)
    amount_alert_bool = fields.Boolean(string='Amount Alert Bool', compute='_compute_amount_alert_bool', default=False,
                                       store=True)
    company_id = fields.Many2one(comodel_name='res.company', string="Company", required=True, readonly=True,
                                 default=lambda self: self.env.company)
    total_amount = fields.Monetary(string='Total Customer Price', related="work_order_id.total_amount",
                                   store=True)
    vendor_cost = fields.Monetary(string='Total Vendor Cost', related="work_order_id.vendor_cost",
                                  store=True)

    vehicle_id = fields.Many2one(string='Vehicle Number', comodel_name='vehicle.vehicle')
    vehicle_model_id = fields.Many2one(string='Vehicle Model', comodel_name='fleet.vehicle.model',
                                       related='vehicle_id.vehicle_model_id', store=True)
    vehicle_type_id = fields.Many2one(string='Vehicle Type', related='vehicle_id.vehicle_type_id', store=True)
    vehicle_description = fields.Char(string='Vehicle Description')
    package_description = fields.Char(string='Package Description')
    start_date = fields.Date(string='Start date', required=True)
    end_date = fields.Date(string='End date', required=True)
    total_km = fields.Float(string='Total KM')
    quantity = fields.Integer(string='Qty', default=1)
    tonnage = fields.Integer(string='Tonnage', default=1)


    source_id = fields.Many2one("res.state.city")
    destination_id = fields.Many2one("res.state.city")
    sales_person_id = fields.Many2one("hr.employee", string="Sales Person")


    def set_data_from_batch_trip_line_ids(self):
        for rec in self:
            if rec.batch_trip_line_ids:
                rec.vehicle_id = rec.batch_trip_line_ids[0].vehicle_id.id
                rec.vehicle_model_id = rec.batch_trip_line_ids[0].vehicle_model_id.id
                rec.vehicle_type_id = rec.batch_trip_line_ids[0].vehicle_type_id.id
                rec.vehicle_description = rec.batch_trip_line_ids[0].vehicle_description
                rec.package_description = rec.batch_trip_line_ids[0].package_description
                rec.start_date = rec.batch_trip_line_ids[0].start_date
                rec.end_date = rec.batch_trip_line_ids[0].end_date
                rec.total_km = rec.batch_trip_line_ids[0].total_km
                rec.quantity = rec.batch_trip_line_ids[0].quantity
                rec.tonnage = rec.batch_trip_line_ids[0].tonnage
                rec.source_id = rec.batch_trip_line_ids[0].source_id.id
                rec.destination_id = rec.batch_trip_line_ids[0].destination_id.id

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(BatchTripFTL, self).get_view(view_id=view_id, view_type=view_type, **options)
        doc = etree.XML(res['arch'])
        user = self.env.user
        if view_type in ['form', 'tree']:
            doc = self._set_permissions(doc, user)
            res['arch'] = etree.tostring(doc)
        return res

    def _set_permissions(self, doc, user):

        if not user.has_group('fleet.fleet_group_manager') and not user.has_group(
                'fleet_ftl.group_ftl_user'):
            for node in doc.xpath("//form | //tree"):
                node.set("create", 'false')

        if not user.has_group('fleet.fleet_group_manager') and not user.has_group(
                'fleet_ftl.group_ftl_enable_edit'):
            for node in doc.xpath("//form | //tree"):
                node.set("edit", 'false')
                if node.tag == 'tree':
                    node.set("delete", 'false')

        return doc


    @api.depends('work_order_amount', 'total_trip_amount')
    def _compute_amount_alert_bool(self):
        for rec in self:
            if rec.work_order_amount and rec.total_trip_amount:
                if rec.work_order_amount != rec.total_trip_amount:
                    rec.amount_alert_bool = True
                else:
                    rec.amount_alert_bool = False
            else:
                rec.amount_alert_bool = False
        return True

    @api.onchange('work_order_id')
    def onchange_work_order(self):
        """validate if a trip is already linked with single trip work order"""
        for rec in self:
            if rec.work_order_id and rec.work_order_id.wo_type_id.is_single_trip:
                if rec.work_order_id.batch_trip_ids:
                    for trip in rec.work_order_id.batch_trip_ids:
                        if trip.state != 'rejected':
                            raise UserError(_('Cannot add more trips to single trip work order'))

                rec.start_date = rec.work_order_id.delivery_date_from
                rec.end_date = rec.work_order_id.delivery_date_to
                rec.total_trip_amount = rec.work_order_id.total_amount
                if rec.work_order_id.work_order_line_ids:
                    rec.tonnage = rec.work_order_id.work_order_line_ids[0].tonnage

    @api.constrains('trip_date', 'work_order_id')
    def check_back_days(self):
        today = fields.Date.today()
        for rec in self:
            back_date = False
            ftl_back_days = rec.company_id.ftl_back_days or 0

            if ftl_back_days > 0:
                ftl_back_days -= 1
                back_date = today - timedelta(days=ftl_back_days)

            if back_date and rec.trip_date < back_date:
                raise UserError(
                    _("Not allowed to create back-dated trips more than %s day(s) old.") % ftl_back_days)
            elif not rec.work_order_id.delivery_date_from:
                raise UserError(
                    _("Not allowed to create trips with the work order without date."))
            elif rec.trip_date < rec.work_order_id.delivery_date_from:
                raise UserError(
                    _("Not allowed to create back-dated trips before the work order date."))
            elif rec.trip_date > today:
                raise UserError(
                    _("Not allowed to create future-dated trips."))

    @api.model
    def create(self, vals):
        """Inherits create function to generate ftl daily trip sequence"""
        company_id = self.env.company.id
        sequence = self.env['ir.sequence'].search(
            [('company_id', '=', company_id), ('code', '=', 'fleet.ftl.dt.seq')])
        if not sequence:
            sequence = self.env['ir.sequence'].search([('code', '=', 'fleet.ftl.dt.seq')], limit=1)
            new_sequence = sequence.sudo().copy()
            new_sequence.company_id = company_id
            code = new_sequence.next_by_id()
        else:
            code = self.env['ir.sequence'].next_by_code('fleet.ftl.dt.seq')
        vals['name'] = code
        res = super().create(vals)
        for rec in res:
            if vals.get('ftl_multi_attachment_ids'):
                rec.ftl_multi_attachment_ids.res_id = rec.id
        return res

    @api.onchange('trip_date')
    def _onchange_trip_date(self):
        for res in self:
            res.write({'start_date': res.trip_date, 'end_date': res.work_order_id.delivery_date_to})

    def print_ftl_xlsx(self):
        for rec in self:
            data = {
                'ids': rec.env.context.get('active_ids', []),
                'model': 'batch.trip.ftl',
            }
            report = rec.env.ref('fleet_ftl.ftl_batch_trip_xlsx')
            report.report_file = "Ftl_Trip_%s" % (rec.trip_date or '')
            return rec.env.ref('fleet_ftl.ftl_batch_trip_xlsx').report_action(rec, data=data)

    def action_ftl_send_for_approval(self):
        """Function to change state from new to pending_approval"""
        for rec in self:
            if rec.work_order_id.customer_id != rec.customer_id:
                raise UserError(
                    f"The customer does not match the customer "
                    f" associated with the work order({rec.work_order_id.customer_id.name}).")
            if rec.work_order_id.vendor_id != rec.vendor_id:
                raise UserError(
                    f"The vendor does not match the vendor "
                    f"associated with the work order ({rec.work_order_id.vendor_id.name}).")
            if rec.state != 'new':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('Trip is in %s state.Please Refresh' % (state)))
            if not rec.end_date:
                raise UserError(_("Please add end date in trip before sending for approve."))
            if not rec.source_id:
                raise UserError(_("Please add Source in trip before sending for approve."))
            if not rec.destination_id:
                raise UserError(_("Please add Destination in trip before sending for approve."))

            ctx = {'function': 'action_ftl_send_for_approval_ftl_batch_trip'}
            form_view_id = self.env.ref('fleet_ftl.ftl_user_action_history_form').id
            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'ftl.user.action.history',
                'type': 'ir.actions.act_window',
                'view_id': form_view_id
            }

    def action_ftl_trip_finance_approve(self):
        """Function to change state from ops_approved to finance_approved"""
        for rec in self:
            if rec.state != 'ops_approved':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('Trip is in %s state.Please Refresh' % (state)))

            ctx = {'function': 'action_ftl_trip_finance_approve_ftl_batch_trip'}
            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'ftl.user.action.history',
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref('fleet_ftl.ftl_user_action_history_form').id
            }

    def action_ftl_ops_approve(self):
        """Function to change state from pending_approval to ops_approved"""
        for rec in self:
            if rec.state != 'pending_approval':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('Trip is in %s state.Please Refresh' % (state)))

            ctx = {'function': 'action_ftl_ops_approve_ftl_batch_trip'}
            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'ftl.user.action.history',
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref('fleet_ftl.ftl_user_action_history_form').id
            }

    def action_ftl_trip_complete(self):
        """Function to change state from finance_approved to completed"""
        for rec in self:
            if rec.state != 'finance_approved':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('Trip is in %s state.Please Refresh' % (state)))
            if not rec.pod_attachment:
                raise UserError(
                    _('Cannot Complete Trip Without Proof Of Delivery Please Attach the Document on POD Attachment'))

            ctx = {'function': 'action_ftl_trip_complete_ftl_batch_trip'}
            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'ftl.user.action.history',
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref('fleet_ftl.ftl_user_action_history_form').id
            }

    def action_ftl_trip_rejected(self):
        """Function to change state to rejected and invoice state to nothing_to_invoice"""
        for rec in self:
            if rec._context.get('button_user') == 'group_ftl_approver':
                if rec.state != 'pending_approval':
                    state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                    raise UserError(_('Trip is in %s state.Please Refresh' % (state)))

            if rec._context.get('button_user') == 'ftl_finance_manger':
                if rec.state != 'ops_approved':
                    state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                    raise UserError(_('Trip is in %s state.Please Refresh' % (state)))

        ctx = {'function': 'action_ftl_trip_rejected_ftl_batch_trip'}
        return {
            'name': _('Comments'),
            'view_type': 'form',
            'target': 'new',
            'context': ctx,
            "view_mode": 'form',
            'res_model': 'ftl.user.action.history',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('fleet_ftl.ftl_user_action_history_form').id
        }

    def action_ftl_return(self):
        """Function to return to previous state, show UserError if tried of completed, rejected record"""
        for rec in self:

            if rec._context.get('button_user') == 'group_ftl_approver':
                if rec.state != 'pending_approval':
                    state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                    raise UserError(_('Trip is in %s state.Please Refresh' % (state)))
            if rec._context.get('button_user') == 'ftl_finance_manger':
                if rec.state != 'ops_approved':
                    state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                    raise UserError(_('Trip is in %s state.Please Refresh' % (state)))
            if self.state == 'completed':
                raise UserError(_(
                    'The trip has been completed already'))
            if self.state == 'rejected':
                raise UserError(_(
                    'The trip has been rejected already'))

            ctx = {
                'current_state': self.state,
                'function': 'action_ftl_return_ftl_batch_trip'
            }
            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'ftl.user.action.history',
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref('fleet_ftl.ftl_user_action_history_form').id
            }

    def _compute_is_editable(self):
        """function to compute edit access for different group users"""
        for rec in self:
            if rec.state == 'new':
                if self.env.user.has_group('fleet_ftl.group_ftl_user') or self.env.user.has_group(
                        'fleet.fleet_group_manager'):
                    rec.is_editable = True
                else:
                    rec.is_editable = False
            elif rec.state == 'pending_approval':
                if self.env.user.has_group('fleet_ftl.group_ftl_approver') or self.env.user.has_group(
                        'fleet.fleet_group_manager'):
                    rec.is_editable = True
                else:
                    rec.is_editable = False
            elif rec.state == 'ops_approved':
                rec.is_editable = False
            else:
                rec.is_editable = False

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    args.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    args.append(('region_id', 'in', []))
        res = super(BatchTripFTL, self).search(args, offset, limit, order, count=count)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    domain.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    domain.append(('region_id', 'in', []))
        return super(BatchTripFTL, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)

    @api.onchange('customer_id')
    def onchange_customer_id(self):
        """set customer region as default region"""
        for rec in self:
            rec.region_id = rec.customer_id.region_id and rec.customer_id.region_id.id or False
            rec.work_order_id = False if rec.work_order_id.customer_id != rec.customer_id else rec.work_order_id.id
            rec.sales_person_id = rec.customer_id.order_sales_person

    def unlink(self):
        if not self.env.user.has_group('fleet.fleet_group_manager'):
            raise UserError(_("You are not allowed to delete the trip."))

        non_deletable_states = [rec.state for rec in self if rec.state not in ('new', 'rejected')]
        if non_deletable_states:
            raise UserError(_("You cannot delete the trip when it is not in 'new' or 'rejected' state."))

        return super(BatchTripFTL, self).unlink()


    def action_send_to_customer(self):
        """this function used to send mail to customer about the ftl trip summary"""
        self.ensure_one()
        try:
            compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        except ValueError:
            compose_form_id = False

        batch_trip_report_id = self.env.ref('fleet_ftl.ftl_batch_trip_xlsx')
        generated_report = self.env['ir.actions.report'].sudo()._render_xlsx(batch_trip_report_id, [self.id],
                                                                             data=self.env.context)
        data_record = base64.b64encode(generated_report[0])

        ir_values = {
            'name': 'Batch Trip FTL.xlsx',
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/vnd.ms-excel',
            'res_model': 'batch.trip.ftl',
        }
        attachment = self.env['ir.attachment'].sudo().create(ir_values)
        email_template = self.env.ref('fleet_ftl.batch_trip_ftl_send_to_customer_email_template')
        email_template.write({'attachment_ids': [(6, 0, [attachment.id])]})

        ctx = {
            'default_model': 'batch.trip.ftl',
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

    def get_email_to(self):
        """ get email to"""
        joined_string = ""
        for record in self:
            group_obj = False
            approval_group = False
            emails = [self.env.user.partner_id.email or '']
            user_action = self.env['ftl.user.action.history'].search([('batch_trip_ftl_id', '=', record.id)], limit=1,
                                                                     order='id desc')

            if record.create_uid.partner_id.email not in emails:
                if not self.env.context.get('from_return', False) or (
                        self.env.context.get('from_return', False) and user_action.action != 'Ops Approved'):
                    emails.append(record.create_uid.partner_id.email or '')

            if self.env.context.get('from_send_for_approve', False):
                group_obj = self.env.ref('fleet_ftl.group_ftl_approver')
                approval_group = self.env.ref('fleet_ftl.group_notify_ftl_trip_ops_approve')

            elif self.env.context.get('from_ops_approve', False):
                group_obj = self.env.ref('fleet_ftl.ftl_finance_manger')
                approval_group = self.env.ref('fleet_ftl.group_notify_ftl_trip_finance_approve')

            elif self.env.context.get('from_finance_approve', False):
                group_obj = self.env.ref('fleet_ftl.group_notify_ftl_trip_complete')
                approval_group = self.env.ref('fleet_ftl.group_notify_ftl_trip_complete')

            elif user_action and user_action.action == 'Ops Approved' and (
                    self.env.context.get('from_return', False) or self.env.context.get('from_reject', False)):
                if user_action.user_id.partner_id.email not in emails:
                    emails.append(user_action.user_id.partner_id.email or '')

            if group_obj and approval_group:
                for user in approval_group.users:
                    if user.partner_id.email not in emails:
                        emails.append(user.partner_id.email or '')
            if emails:
                joined_string = ",".join(emails)
        return joined_string

    def get_company_wise(self, company, trip_list, total_revenue, total_cost):
        total_margin = (total_revenue - total_cost) or 0.0
        total_margin_percentage = 0.0
        if total_revenue > 0.0:
            total_margin_percentage = ((total_margin / total_revenue) * 100) or 0.0
        grand_total = {
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'total_margin': total_margin,
            'total_margin_percentage': total_margin_percentage,
        }
        company_wise = {
            'company_name': company.display_name,
            'data': trip_list,
            'total': grand_total}
        return company_wise

    def action_get_customer_wise_data(self, start_date, end_date):
        """
        Get work order wise data
        """
        daily_trips = self.env['batch.trip.ftl'].search([('state', 'in', ('finance_approved', 'completed')),
                                                         ('trip_date', '>=', start_date),
                                                         ('trip_date', '<=', end_date)])
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
                        revenue = sum(customer_wise_trip.mapped('total_trip_amount')) or 0.0
                        cost = sum((customer_wise_trip.mapped('work_order_id')).mapped('vendor_cost')) or 0.0
                        margin = (revenue - cost) or 0.0
                        margin_percentage = 0.0
                        if revenue > 0.0:
                            margin_percentage = ((margin / revenue) * 100) or 0.0
                        vals = {
                            'customer': customer.name,
                            'region': customer.region_id.name,
                            'revenue': revenue,
                            'cost': cost,
                            'margin': margin,
                            'margin_percentage': margin_percentage,
                        }
                        customer_wise_trip_list.append(vals)
                        total_revenue += revenue or 0.0
                        total_cost += cost or 0.0
                if customer_wise_trip_list:
                    company_wise_trip_list.append(
                        self.get_company_wise(company, customer_wise_trip_list, total_revenue, total_cost))

        return company_wise_trip_list

    def action_get_region_wise_data(self, start_date, end_date):
        """
        Get region wise data
        """
        daily_trips = self.env['batch.trip.ftl'].search([('state', 'in', ('finance_approved', 'completed')),
                                                         ('trip_date', '>=', start_date),
                                                         ('trip_date', '<=', end_date)])
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
                        revenue = sum(region_wise_trip.mapped('total_trip_amount')) or 0.0
                        cost = sum((region_wise_trip.mapped('work_order_id')).mapped('vendor_cost')) or 0.0
                        margin = (revenue - cost) or 0.0
                        margin_percentage = 0.0
                        if revenue > 0.0:
                            margin_percentage = ((margin / revenue) * 100) or 0.0
                        vals = {
                            'region': region.name,
                            'revenue': revenue,
                            'cost': cost,
                            'margin': margin,
                            'margin_percentage': margin_percentage,
                        }
                        region_wise_trip_list.append(vals)
                        total_revenue += revenue or 0.0
                        total_cost += cost or 0.0
                if region_wise_trip_list:
                    company_wise_trip_list.append(
                        self.get_company_wise(company, region_wise_trip_list, total_revenue, total_cost))

        return company_wise_trip_list

    def action_send_revenue_report(self, month=False):
        """
        Cron function: for sending daily/monthly revenue report
        """
        if month:
            template = self.env.ref('fleet_ftl.mail_template_ftl_monthly_revenue_report')
        else:
            template = self.env.ref('fleet_ftl.mail_template_ftl_daily_revenue_report')
        if template:
            users = self.env.ref('fleet_ftl.group_send_ftl_revenue_report').users
            res = self.env['res.users'].search_read([('id', 'in', users.ids)], ['email'])
            emails = set(r['email'] for r in res if r.get('email'))
            if month:
                dt = date.today().replace(day=1)
                end_date = dt - timedelta(days=1)
            else:
                end_date = date.today() + timedelta(days=-1)
            start_date = end_date.replace(day=1)
            email_values = {
                'start_date': start_date.strftime("%d-%m-%Y"),
                'end_date': end_date.strftime("%d-%m-%Y"),
                'month': start_date.strftime("%b %Y"),
                'revenue_for_customer': self.action_get_customer_wise_data(start_date, end_date),
                'revenue_for_region': self.action_get_region_wise_data(start_date, end_date),
            }
            template.with_context(email_values).send_mail(self.id, email_values={'email_to': ','.join(emails)},
                                                          force_send=True)

