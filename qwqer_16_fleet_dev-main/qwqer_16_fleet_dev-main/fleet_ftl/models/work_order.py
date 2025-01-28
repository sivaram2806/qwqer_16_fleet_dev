# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo import SUPERUSER_ID

from odoo.tools import formatLang

PAYMENT_TYPE = [
    ("flat", "Flat"), 
    ("percentage", "Percentage")
]
PAYMENT_PERCENTAGE = [
    ("10", "10%"),
    ("20", "20%"),
    ("30", "30%"),
    ("40", "40%"),
    ("50", "50%"),
    ("60", "60%"),
    ("70", "70%"),
    ("80", "80%"),
    ("90", "90%"),
    ("100", "100%")
]



class WorkOrderType(models.Model):
    """
    Model contains records from work order type, #V13_model name: work.order.type
    """
    _name = 'work.order.type'
    _description = "Work Order Type"

    sequence = fields.Integer(string='Sequence')
    name = fields.Char(string='Type')  # V13_field: type
    code = fields.Char(string='Code')  # V13_field: code
    active = fields.Boolean(string="Active", default=True,
                            help="If unchecked, it will allow you to hide the quotation template without removing it.")
    is_single_trip = fields.Boolean(string='Is Single Trip')
    company_id = fields.Many2one(comodel_name='res.company', string="Company", required=True, readonly=True,
                                 default=lambda self: self.env.company)


class WorkOrderLine(models.Model):
    """
    Model contains records from work order line, #V13_model name: work.order.line
    """
    _name = 'work.order.line'
    _description = "Work Order Line"

    sequence = fields.Char(string='Sequence')
    work_order_id = fields.Many2one(comodel_name='work.order', string="Work Order",
                                    ondelete='cascade', copy=True)
    description = fields.Text(string='Load Description')
    lr_num = fields.Char(string='LR Number')
    due_on = fields.Date(string='Due On', default=fields.Date.today)
    uom = fields.Many2one(comodel_name='uom.uom', string='Unit')  # V13_field: unit, model: 'uom.uom'
    quantity = fields.Float(string="Qty", default=1)
    tonnage = fields.Float(string="Tonnage")
    currency_id = fields.Many2one(comodel_name='res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id)
    unit_price = fields.Monetary(string="Unit Price")
    total = fields.Monetary(string="Total", compute='_compute_total')
    company_id = fields.Many2one(comodel_name='res.company', string="Company", required=True, readonly=True,
                                 default=lambda self: self.env.company)

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.quantity * rec.unit_price


class WorkOrder(models.Model):
    """
    Model contains records from work order, #V13_model name: work.order
    """
    _name = 'work.order'
    _description = "Work Order"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Name')
    contract_id = fields.Many2one(comodel_name='vehicle.contract', string='Contract',
                                  tracking=True)
    region_id = fields.Many2one(comodel_name='sales.region', string='Region', domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    customer_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True,
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False),"
                                       " ('customer_rank','>', 0), ('service_type_id.is_fleet_service','=',True),('is_ftl_customer','=',True)]")
    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor', required=True,
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False),"
                                       " ('supplier_rank','>', 0), ('service_type_id.is_fleet_service','=',True)]")
    payment_term_id = fields.Many2one(comodel_name='account.payment.term', string='Payment Terms')
    wo_type_id = fields.Many2one(comodel_name='work.order.type',
                                 string='Work Order Type', default=lambda self: self.get_default_work_order_type())   # V13_field: workorder_type_id
    shipping_id = fields.Many2one(comodel_name="delivery.carrier", string="Shipping Method")
    delivery_date_from = fields.Date(string='Delivery Date From')
    delivery_date_to = fields.Date(string='Delivery Date To')
    currency_id = fields.Many2one(comodel_name='res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id)
    customer_price = fields.Monetary(string='Total Customer Price')
    vendor_cost = fields.Monetary(string='Total Vendor Cost')
    adv_payment_type = fields.Selection(PAYMENT_TYPE, string='Adv. Payment Type',
                                        default=PAYMENT_TYPE[0][0], copy=False, required=True)
    adv_payment_percentage = fields.Selection(PAYMENT_PERCENTAGE, string='Adv. Payment Percentage', copy=False)
    adv_amount = fields.Monetary(string='Adv. Amount', compute='_compute_advance_amount')
    vendor_code = fields.Char(string='Vendor Code')
    driver_phone = fields.Char(string='Driver Phone')
    shipping_address = fields.Text(string='Shipping Address')
    pick_up_loc = fields.Text(string='Pick Up From')  # V13_field: pick_up_from
    quotation_ref = fields.Char(string='Quotation Reference')  # V13_field: quotation_reference
    work_order_line_ids = fields.One2many(comodel_name='work.order.line', string="Work Order Line",
                                          inverse_name='work_order_id', copy=False)
    total_amount = fields.Monetary(string='Total Customer Price', digits='Product Price',
                                   compute='_compute_total_amount', store=True)
    payment_ids = fields.One2many(comodel_name='account.payment', inverse_name='work_order_id', copy=False)
    move_ids = fields.Many2many(comodel_name='account.move', relation="account_move_work_order", column1="move_id",
                                column2='work_order_id')
    bill_move_ids = fields.One2many(comodel_name='account.move', inverse_name='work_order_id', copy=False)
    batch_trip_ids = fields.One2many(comodel_name='batch.trip.ftl', inverse_name='work_order_id', copy=False)

    vendor_advance_paid = fields.Monetary(string='Vendor Adv. Paid', digits='Product Price',
                                 compute='_compute_total_amount', store=True)
    bill_amount = fields.Monetary(string='Bill Amount', digits='Product Price',
                               compute='_compute_total_amount', store=True)

    invoice_amount = fields.Monetary(compute='_compute_total_amount', store=True)
    amount_payable = fields.Monetary(compute='_compute_total_amount', store=True)
    amount_receivable = fields.Monetary(compute='_compute_total_amount', store=True)

    payment_count = fields.Integer(string='Payment Count', compute='_compute_count', store=True)
    trip_count = fields.Integer(string='Trip Count', compute='_compute_count', store=True)
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_count', store=True)
    bill_count = fields.Integer(string='Bill Count', compute='_compute_count', store=True)
    user_action_ids = fields.One2many(comodel_name='ftl.user.action.history', inverse_name='work_order_id', copy=False)
    state = fields.Selection(selection=[
        ("new", "New"),
        ("pending_approval", "Pending Approval"),
        ("mu_approve", "MU Approved"),
        ("finance_approve", "Finance Approved"),
        ("rejected", "Rejected")], default="new", copy=False, tracking=True)
    is_editable = fields.Boolean(string='Is Editable', compute='_compute_is_editable', default=True, copy=False)
    attachment_ids = fields.Many2many(comodel_name='ir.attachment', relation='ftl_wo_attachment',
                                      column1='attachment_id', column2='ftl_wo_id', string="Attachments", copy=False)
    company_id = fields.Many2one(comodel_name='res.company', string="Company", required=True, readonly=True,
                                 default=lambda self: self.env.company.id)
    invoice_state = fields.Selection([
                              ("to_invoice", "To Invoice"),
                              ("paid", "Pre paid"),
                              ("partial", "Partially Paid"),
                              ("not_paid", "To Pay")], string='Invoice Status',
                              default="to_invoice", copy=False, tracking=True)
    sales_person_id = fields.Many2one("hr.employee", string="Sales Person", )
    customer_credit_warning = fields.Text(compute='_check_customer_credit_limit_warning', store=True)
    is_credit_warning_visible = fields.Boolean(readonly=True, default=False, copy=False, compute='_check_customer_credit_limit_warning', store=True)


    _sql_constraints = [
        ('driver_phone_numeric', 'CHECK(driver_phone ~ \'^[0-9]{10}$\')',
         'Invalid characters or more than 10 digits in driver phone number !'),
    ]

    def get_default_work_order_type(self):
        work_order_type = self.env['work.order.type'].search([("is_single_trip", "!=", False), ('company_id', "=", self.env.company.id)])
        return work_order_type and work_order_type[0].id

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        for wo in self:
            wo = wo.with_company(wo.company_id)
            wo.payment_term_id = wo.customer_id.property_payment_term_id
            wo.sales_person_id = wo.customer_id.order_sales_person

    @api.model
    def create(self, vals):
        # generating sequence for work order
        company_id = self.env.company.id
        sequence = self.env['ir.sequence'].search(
            [('company_id', '=', company_id), ('code', '=', 'fleet.ftl.wo.seq')])
        if not sequence:
            sequence = self.env['ir.sequence'].search([('code', '=', 'fleet.ftl.wo.seq')], limit=1)
            new_sequence = sequence.sudo().copy()
            new_sequence.company_id = company_id
            code = new_sequence.next_by_id()
        else:
            code = self.env['ir.sequence'].next_by_code('fleet.ftl.wo.seq')
        vals['name'] = code

        res = super(WorkOrder, self).create(vals)
        if vals.get('attachment_ids'):
            res.attachment_ids.res_id = res.id
        workorder_lines = res.work_order_line_ids.filtered(lambda s: s.total <= 0.0)
        if workorder_lines:
            raise UserError(_("Total amount should be greater 0."))
        if res.contract_id:
            res.contract_id.write({'wo_ids': [(4, res.id)]})
            if res.contract_id.parent_id:
                if res.contract_id.parent_id.state not in ('expired', 'closed'):
                    res.contract_id.parent_id.write({'wo_ids': [(4, res.id)]})
                if res.contract_id.parent_id.child_ids:
                    child_contracts = res.contract_id.parent_id.child_ids.filtered(
                        lambda s: s.state not in ('expired', 'closed') and s.id != res.contract_id.id)
                    if child_contracts:
                        child_contracts.write({'wo_ids': [(4, res.id)]})
            elif res.contract_id.child_ids:
                child_contracts = res.contract_id.child_ids.filtered(
                    lambda s: s.state not in ('expired', 'closed') and s.id != res.contract_id.id)
                if child_contracts:
                    child_contracts.write({'wo_ids': [(4, res.id)]})
        res._check_customer_credit_limit_warning()
        return res

    def write(self, vals):
        for rec in self:
            if 'contract_id' in vals and rec.contract_id:
                if rec.contract_id.state not in ('expired', 'closed'):
                    rec.contract_id.write({'wo_ids': [(3, rec.id)]})
                if rec.contract_id.parent_id:
                    if rec.contract_id.parent_id.state not in ('expired', 'closed'):
                        rec.contract_id.parent_id.write({'wo_ids': [(3, rec.id)]})
                    if rec.contract_id.parent_id.child_ids:
                        child_contracts = rec.contract_id.parent_id.child_ids.filtered(
                            lambda s: s.state not in ('expired', 'closed') and s.id != rec.contract_id.id)
                        if child_contracts:
                            child_contracts.write({'wo_ids': [(3, rec.id)]})
                elif rec.contract_id.child_ids:
                    child_contracts = rec.contract_id.child_ids.filtered(
                        lambda s: s.state not in ('expired', 'closed') and s.id != rec.contract_id.id)
                    if child_contracts:
                        child_contracts.write({'wo_ids': [(3, rec.id)]})
            res = super(WorkOrder, self).write(vals)
            workorder_lines = rec.work_order_line_ids.filtered(lambda s: s.total <= 0.0)
            if workorder_lines:
                raise UserError(_("Total amount should be greater 0."))
            if 'contract_id' in vals:
                rec.contract_id.write({'wo_ids': [(4, rec.id)]})
                if rec.contract_id.parent_id:
                    if rec.contract_id.parent_id.state not in ('expired', 'closed'):
                        rec.contract_id.parent_id.write({'wo_ids': [(4, rec.id)]})
                    if rec.contract_id.parent_id.child_ids:
                        child_contracts = rec.contract_id.parent_id.child_ids.filtered(
                            lambda s: s.state not in ('expired', 'closed') and s.id != rec.contract_id.id)
                        if child_contracts:
                            child_contracts.write({'wo_ids': [(4, rec.id)]})
                elif rec.contract_id.child_ids:
                    child_contracts = rec.contract_id.child_ids.filtered(
                        lambda s: s.state not in ('expired', 'closed') and s.id != rec.contract_id.id)
                    if child_contracts:
                        child_contracts.write({'wo_ids': [(4, rec.id)]})

            return res

    def unlink(self):
        for rec in self:
            if not self.env.user.has_group('fleet.fleet_group_manager'):
                raise UserError(_("You are not allowed to delete the work order."))
            if rec.state not in ('new', 'reject'):
                raise UserError(_("You cannot delete the work order when it is not in 'new' or 'rejected' state."))
        return super(WorkOrder, self).unlink()

    @api.depends('work_order_line_ids', 'work_order_line_ids.total', 'payment_ids.state', 'payment_ids.amount', 'move_ids.state',
                 'move_ids.amount_total', 'bill_move_ids.state', 'bill_move_ids.amount_total')
    def _compute_total_amount(self):
        for rec in self:
            if rec.work_order_line_ids:
                line_total = sum(rec.work_order_line_ids.mapped('total'))
                if line_total>0:
                    rec._check_customer_credit_limit_warning(line_total)

                    rec.total_amount = line_total

                all_invoices = rec.move_ids.filtered(lambda s:s.state == 'posted' and s.move_type == 'out_invoice')
                rec.invoice_amount = sum(all_invoices.mapped("amount_total"))
                rec.amount_receivable = sum(all_invoices.mapped("amount_residual"))

                posted_payments = rec.payment_ids.filtered(lambda s: s.state == 'posted' and s.payment_type == 'outbound')
                rec.vendor_advance_paid = sum(posted_payments.mapped('amount'))

                posted_vendor_bills = rec.bill_move_ids.filtered(lambda s: s.state == 'posted' and s.move_type == 'in_invoice')
                rec.bill_amount = sum(posted_vendor_bills.mapped('amount_total'))
                rec.amount_payable = sum(posted_vendor_bills.mapped("amount_residual")) - rec.vendor_advance_paid

    @api.depends('work_order_line_ids', 'work_order_line_ids.total', 'payment_ids.state', 'payment_ids.amount', 'move_ids.state')
    def _check_customer_credit_limit_warning(self, current_wo_amt=0):
        for rec in self:
            if rec.company_id.customer_credit_limit and rec.customer_id.active_limit:
                # (1) customer payable amount
                invoice_payable = rec.customer_id.credit
                # (2) total non-invoiced WO amount
                non_invoiced_wo = rec.env["work.order"].search(
                        [('customer_id', '=', rec.customer_id.id), ('invoice_count', "=", 0),
                         ('state', "not in", ['rejected']), ('id', "not in", rec.ids)])
                non_invoiced_wo_amt = sum(non_invoiced_wo.mapped('total_amount'))
                # (3) current WO amount
                current_wo_total = current_wo_amt
                # sum of (1), (2) and (3)
                total_receivable = invoice_payable + non_invoiced_wo_amt + current_wo_total

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
                if total_receivable > rec.customer_id.blocking_stage:
                    raise UserError(
                        _("Customer's existing Trip total payable due has exceeded available credit limit of %s.",
                          (formatLang(rec.env, rec.customer_id.blocking_stage,
                                      currency_obj=rec.company_id.currency_id))))
            else:
                rec.is_credit_warning_visible = False
                rec.customer_credit_warning = False

    @api.depends('adv_payment_type', 'adv_payment_percentage','vendor_cost')
    def _compute_advance_amount(self):
        for rec in self:
            rec.adv_amount = 0
            if rec.adv_payment_type == 'percentage':
                rec.adv_amount = (rec.vendor_cost/100) * int(rec.adv_payment_percentage)

    def action_view_trip(self):
        for rec in self:
            return {
                'name': _('Trips'),
                'res_model': 'batch.trip.ftl',
                'view_mode': 'list,form',
                'domain': [('work_order_id', '=', rec.id)],
                'context': {'create': False},
                'target': 'current',
                'type': 'ir.actions.act_window',
            }

    def action_view_invoice(self):
        for rec in self:
            context = dict(self._context)
            context.update({'from_fleet': True, 'create': False})
            return {
                'name': _('Invoices'),
                'res_model': 'account.move',
                'view_mode': 'list,form',
                'context': context,
                'domain': [('id', 'in', rec.move_ids.ids), ('move_type', '=', 'out_invoice')],
                'target': 'current',
                'type': 'ir.actions.act_window',
            }

    def action_view_bill(self):
        for rec in self:
            context = dict(self._context)
            context.update({'from_fleet': True, 'create': False})
            return {
                'name': _('Bills'),
                'res_model': 'account.move',
                'view_mode': 'list,form',
                'context': context,
                'domain': [('work_order_id', '=', rec.id), ('move_type', '=', 'in_invoice')],
                'target': 'current',
                'type': 'ir.actions.act_window',
            }

    def action_view_payment(self):
        for rec in self:
            return {
                'name': _('Payments'),
                'res_model': 'account.payment',
                'view_mode': 'list,form',
                'domain': [('work_order_id', '=', rec.id)],
                'target': 'current',
                'context': {'create': False, 'from_work_order': True},
                'type': 'ir.actions.act_window',
            }

    @api.depends("move_ids", "payment_ids", "batch_trip_ids", "bill_move_ids")
    def _compute_count(self):
        for rec in self:
            rec.payment_count = len(rec.payment_ids)
            rec.trip_count = len(rec.batch_trip_ids)
            rec.invoice_count = len(rec.move_ids.filtered(lambda s: s.move_type == 'out_invoice'))
            rec.bill_count = len(rec.bill_move_ids.filtered(lambda s: s.move_type == 'in_invoice'))

    def action_send_for_approve(self):
        """Function to change state from new to pending_approval, only if there is work order line"""
        for rec in self:
            if rec.state != 'new':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('Work order is in %s state.Please refresh the page' % (state)))
            messages = [] # List to store validation error messages

            # Check for each required field and append corresponding message if missing
            if not rec.attachment_ids:
                messages.append("Attachments")
            if not rec.work_order_line_ids:
                messages.append("Work order line")
            if not rec.delivery_date_from or not rec.delivery_date_to:
                messages.append("Delivery Period")
            if not rec.vendor_cost:
                messages.append("Vendor cost")

            # Raise a validation error if any messages were added
            if messages:
                if len(messages) > 1:
                    message_text = ', '.join(messages[:-1]) + ' and ' + messages[-1]
                else:
                    message_text = messages[0]

                raise ValidationError(
                    f"Please fill in the following details to proceed:\n- {message_text}"
                )

        ctx = {'function': 'action_sent_for_approval_ftl_wo'}
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

    def action_return(self):
        """Function to return to previous state"""
        for rec in self:
            if rec.state in ('new', 'reject', 'finance_approve'):
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('Work order is in %s state.Please refresh the page' % (state)))
            if rec._context.get('button_mu_user', False):
                if rec.state != 'pending_approval':
                    state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                    raise UserError(_('Work order is in %s state.Please refresh the page' % (state)))
            if rec._context.get('button_finance_user', False):
                if rec.state != 'mu_approve':
                    state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                    raise UserError(_('Work order is in %s state.Please refresh the page' % (state)))
            ctx = {'function': 'action_return_ftl_wo'}
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

    def action_mu_approve(self):
        """Function to change state to pending_approval from mu_approve"""
        for rec in self:
            if rec.state != 'pending_approval':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('Work order is in %s state. Please refresh the page' % (state)))
            ctx = {'function': 'action_mu_approve_ftl_wo'}
            form_view_id = rec.env.ref('fleet_ftl.ftl_user_action_history_form').id
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

    def action_finance_approve(self):
        """Function to change state to finance_approve from mu_approve"""
        for rec in self:
            if rec.state != 'mu_approve':
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('Work order is in %s state. Please refresh the page' % (state)))
            ctx = {'function': 'action_finance_approve_ftl_wo'}
            form_view_id = rec.env.ref('fleet_ftl.ftl_user_action_history_form').id
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

    def action_reject(self):
        for rec in self:
            if rec.state in ('reject', 'finance_approve'):
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('Work order is in %s state. Please refresh the page' % (state)))
            if rec._context.get('button_user', False):
                if rec.state != 'new':
                    state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                    raise UserError(_('Work order is in %s state. Please refresh the page' % (state)))
            if rec._context.get('button_mu_user', False):
                if rec.state != 'pending_approval':
                    state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                    raise UserError(_('Work order is in %s state. Please refresh the page' % (state)))
            if rec._context.get('button_finance_user', False):
                if rec.state != 'mu_approve':
                    state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                    raise UserError(_('Work order is in %s state. Please refresh the page' % (state)))
            ctx = {'function': 'action_reject_ftl_wo'}
            form_view_id = rec.env.ref('fleet_ftl.ftl_user_action_history_form').id
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

    def _compute_is_editable(self):
        for rec in self:
            rec.is_editable = True
            if rec.state == 'new':
                if self.env.user.has_group(
                        'fleet_ftl.group_ftl_work_order_send_for_approval') or self.env.user.has_group(
                        'fleet.fleet_group_manager'):
                    rec.is_editable = True
                else:
                    rec.is_editable = False
            elif rec.state == 'pending_approval':
                if self.env.user.has_group(
                        'fleet_ftl.group_ftl_work_order_mu_approve') or self.env.user.has_group(
                        'fleet.fleet_group_manager'):
                    rec.is_editable = True
                else:
                    rec.is_editable = False
            elif rec.state == 'mu_approve':
                if self.env.user.has_group(
                        'fleet_ftl.group_ftl_work_order_finance_approve') or self.env.user.has_group(
                        'fleet.fleet_group_manager'):
                    rec.is_editable = True
                else:
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
        res = super(WorkOrder, self).search(args, offset, limit, order, count=count)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    domain.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    domain.append(('region_id', 'in', []))
        return super(WorkOrder, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)
      
    @api.onchange('customer_id')
    def onchange_customer_id(self):
        """set customer region as default region"""
        for rec in self:
            rec.region_id = rec.customer_id.region_id and rec.customer_id.region_id.id or False
            
    @api.onchange('adv_payment_type')
    def onchange_adv_payment_type(self):
        """ setting advance payment percentage to false when advance payment type is flat"""
        for rec in self:
            if rec.adv_payment_type == 'flat':
                rec.adv_payment_percentage = False
                
    def get_email_to(self):
        """ get email to"""
        joined_string = ""
        for record in self:
            group_obj = False
            approval_group = False
            emails = [self.env.user.partner_id.email or '']
            user_action = self.env['ftl.user.action.history'].search([('work_order_id','=',record.id)],limit=1, order='id desc')
            
            if record.create_uid.partner_id.email not in emails:
                if not self.env.context.get('from_return', False) or (self.env.context.get('from_return', False) and user_action.action != 'MU Approved'):
                    emails.append(record.create_uid.partner_id.email or '')
                    
            if self.env.context.get('from_send_for_approve', False):
                group_obj = self.env.ref('fleet_ftl.group_ftl_work_order_mu_approve')
                approval_group = self.env.ref('fleet_ftl.group_notify_ftl_wo_mu_approve')
                
            elif self.env.context.get('from_mu_approve', False):
                group_obj = self.env.ref('fleet_ftl.group_ftl_work_order_finance_approve')
                approval_group = self.env.ref('fleet_ftl.group_notify_ftl_wo_finance_approve')
            
            elif user_action and user_action.action == 'MU Approved' and (self.env.context.get('from_return', False) or self.env.context.get('from_reject', False)):
                if user_action.user_id.partner_id.email not in emails:
                    emails.append(user_action.user_id.partner_id.email or '')
                        
            if group_obj and approval_group:
                for user in approval_group.users:
                    if user.partner_id.email not in emails:
                        emails.append(user.partner_id.email or '')
            if emails:
                joined_string = ",".join(emails)
        return joined_string
                
