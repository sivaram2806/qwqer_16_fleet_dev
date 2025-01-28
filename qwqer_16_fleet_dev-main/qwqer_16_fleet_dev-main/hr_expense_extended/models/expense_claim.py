# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import models, fields,api, _
from datetime import datetime


class travel_mode(models.Model):
    _name = 'travel.mode'
    _description = 'Model is a configuration for modes of travel'
    _rec_name = 'travel_mode'

    travel_mode = fields.Char()


class HrExpenseExtend(models.Model):
    _inherit = "hr.expense"

    date_from = fields.Date()
    date_to = fields.Date()

    place_from = fields.Char()
    place_to = fields.Char()
    travel_mode = fields.Many2one('travel.mode')

    boarding_date = fields.Date()
    dine = fields.Selection(selection=[
        ('all', 'All'),
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner')
    ])

    lodging_place = fields.Char()
    lodging_hotel_name = fields.Char()

    travel_claim_id = fields.Many2one('hr.expense.claim', string="Travel Claim",
                                      copy=False)
    lodging_claim_id = fields.Many2one('hr.expense.claim', string="Lodging Claim",
                                       copy=False)
    boarding_claim_id = fields.Many2one('hr.expense.claim', string="Boarding Claim",
                                        copy=False)
    other_claim_id = fields.Many2one('hr.expense.claim', string="Other Claim",
                                     copy=False)
    category_type = fields.Selection(related="product_id.category_type", store=True)
    claim_id = fields.Many2one(comodel_name='hr.expense.claim',string="Claim",compute='_compute_claim_id', copy=False, store=True)
    claim_status = fields.Selection(related='claim_id.state', string="Claim State", copy=False, store=True)
    department = fields.Many2one(related='claim_id.department', string="Department", copy=False, store=True)
    expense_manager = fields.Many2one(related='claim_id.expense_manager', string="Expense Manager", copy=False, store=True)

    @api.depends('travel_claim_id', 'lodging_claim_id', 'boarding_claim_id', 'other_claim_id')
    def _compute_claim_id(self):
        for record in self:
            claim_fields = ['travel_claim_id', 'lodging_claim_id', 'boarding_claim_id', 'other_claim_id']
            record.claim_id = next((getattr(record, field) for field in claim_fields if getattr(record, field)), False)
            print(record.claim_id)


class HrExpenseSheetExtend(models.Model):
    _inherit = "hr.expense.sheet"
    def approve_expense_sheets(self):
        if self.env.context.get('model_from') == 'hr.expense.claim':
            self._check_can_approve()
            self._validate_analytic_distribution()
            self._do_approve()
        else:
            res = super(HrExpenseSheetExtend, self).approve_expense_sheets()
            return res

class ExpenseClaim(models.Model):
    """
    Model to create against expense
    """
    _name = 'hr.expense.claim'
    _description = "Expense Claim"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(readonly=True)
    requested_by = fields.Many2one(comodel_name='hr.employee', string="Requested By", required=True, readonly=True,
                                   default=lambda self: self.env.user.employee_id,copy=False,)
    contact_number = fields.Char(string="Contact Number", default=lambda
        self: self.env.user.employee_id.work_phone or self.env.user.employee_id.mobile_phone,copy=False)
    company_id = fields.Many2one(comodel_name='res.company', string="Company", required=True, readonly=True,
                                 default=lambda self: self.env.company,copy=False,)
    state = fields.Selection([
        ("new", "New"),
        ("pending_approval", "Pending Approval"),
        ("mu_approved", "Expense Manager Approved"),
        ("approved_without_advance", "Approved without Advance"),
        ("approved", "Approved"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ], default="new", copy=False, tracking=True)
    expense_approval_stage = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('refused', 'Refused')
    ], string='Status', copy=False, readonly=True, compute='_compute_expense_approval_stage', tracking=True, store=True)
    claim_type = fields.Selection([
        ('travel', 'Travel'),
        ('other', 'Other'), ], string="Claim Type")
    lodging = fields.Selection(selection=[
        ('yes', 'Yes'),
        ('no', 'No')
    ], default='no', copy=False)
    claim_amount = fields.Float(string="Claim Amount")
    claim_reason = fields.Text(string="Claim Reason" ,copy=False)
    is_advance_needed = fields.Boolean(string="Is Advance Needed",copy=False)
    advance_amount = fields.Float(string="Advance Amount",copy=False)
    is_advance_payed = fields.Boolean(copy=False)
    advance_payed_amount = fields.Float(string="Advance Payed Amount",copy=False)
    requested_date = fields.Date(string="Requested Date", default=fields.Date.today,copy=False,)
    expense_date = fields.Date(string="Expense Date")
    department = fields.Many2one(comodel_name='hr.department', string="Department", readonly=True,
                                 default=lambda self: self.env.user.department_id,copy=False,)
    reporting_manager = fields.Many2one(comodel_name='hr.employee', string="Reporting Manager",
                                        readonly=True, default=lambda self: self.env.user.employee_id.parent_id,copy=False,)
    expense_manager = fields.Many2one(comodel_name='res.users', string="Expense Manager", readonly=True,
                                      default=lambda self: self.env.user.employee_id.expense_manager_id,copy=False,)
    mu_approved_by = fields.Many2one(comodel_name='res.users', string="Expense Approved By", readonly=True,copy=False)
    finance_approved_by = fields.Many2one(comodel_name='res.users', string="Finance Approved By", readonly=True,copy=False)
    user_comment = fields.Char(string="User Comment",copy=False)
    mu_comment = fields.Char(string="Expense Manager Comment",copy=False)
    finance_manager_comment = fields.Char(string="Finance Manager Comment",copy=False)
    sheet_id = fields.Many2one('hr.expense.sheet', string="Expense Report", copy=False)
    payment_ids = fields.One2many(comodel_name='account.payment', inverse_name='claim_id', copy=False)
    payment_count = fields.Integer(string='Payment Count', compute='_compute_count', store=True)
    amount_to_pay = fields.Float(string='Amount To Pay', compute='_compute_amount_to_pay', store=True,copy=False)
    amount_to_pay_in = fields.Float(string='Amount To PayIn', compute='_compute_amount_to_pay', store=True,copy=False)
    is_pay_in_done = fields.Boolean(copy=False)
    total_amount = fields.Float(string="Total Amount", compute='_compute_total_amount', store=True,copy=False)
    is_sheet_editable = fields.Boolean(string='Sheet Edit Bool', compute='_compute_is_sheet_editable', default=True,
                                       copy=False)
    have_submit_access = fields.Boolean(string='Have Submit Access', compute='_compute_have_submit_access',
                                        default=False, copy=False)
    travel_exp_line_ids = fields.One2many('hr.expense', 'travel_claim_id', string='Expense Lines',
                                          domain=[("category_type", "=", "travel")], copy=False)
    lodging_exp_line_ids = fields.One2many('hr.expense', 'lodging_claim_id', string='Expense Lines',
                                           domain=[("category_type", "=", "lodging")], copy=False)
    boarding_exp_line_ids = fields.One2many('hr.expense', 'boarding_claim_id', string='Expense Lines',
                                            domain=[("category_type", "=", "boarding")], copy=False)
    other_exp_line_ids = fields.One2many('hr.expense', 'other_claim_id', string='Expense Lines',
                                         domain=[("category_type", "=", "other")], copy=False)
    attachment_ids = fields.Many2many(comodel_name='ir.attachment', relation='expense_attachment',
                                      column1='attachment_id', column2='expense_id', string="Attachments", copy=False)

    def _compute_is_sheet_editable(self):
        """function to compute edit access for different group users"""
        for rec in self:
            if rec.state == 'new':
                rec.is_sheet_editable = True
            elif rec.state == 'pending_approval':
                if self.env.user.has_group('hr_expense_extended.claim_expense_manager_approver'):
                    rec.is_sheet_editable = True
                else:
                    rec.is_sheet_editable = False
            else:
                rec.is_sheet_editable = False

    def _compute_have_submit_access(self):
        """function to compute if user have submitting access for the record"""
        for rec in self:
            rec.have_submit_access = True if self.env.user.id == self.create_uid.id or self.env.user.employee_id == rec.requested_by.id or self.user_has_groups(
                'hr_expense_extended.claim_expense_manager_approver') or self.user_has_groups(
                'hr_expense_extended.expense_claim_admin') else False

    @api.depends('travel_exp_line_ids', 'lodging_exp_line_ids', 'boarding_exp_line_ids', 'other_exp_line_ids')
    def _compute_total_amount(self):
        """computing the total_amount field """
        for rec in self:
            expenses = ['travel_exp_line_ids', 'lodging_exp_line_ids', 'boarding_exp_line_ids', 'other_exp_line_ids']
            expense_amount = []
            for expense in expenses:
                expense_amount.append(sum(rec[expense].mapped('total_amount')))
            rec.total_amount = sum(expense_amount)

    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
    def _compute_expense_approval_stage(self):
        """compute expense approval state"""
        for claim in self:
            if not claim.sheet_id or claim.sheet_id.state == 'draft':
                claim.expense_approval_stage = "draft"
            elif not claim.sheet_id.account_move_id and claim.sheet_id.state != 'done':
                claim.expense_approval_stage = "reported"
            elif claim.sheet_id.state == "cancel":
                claim.expense_approval_stage = "refused"
            elif claim.sheet_id.state == "approve" or claim.sheet_id.state == "post" or claim.sheet_id.state == "done" and claim.sheet_id.payment_state in (
                    'partial', 'in_payment'):
                claim.expense_approval_stage = "approved"
            else:
                claim.expense_approval_stage = "done"
                if claim.amount_to_pay_in == 0 or (claim.amount_to_pay_in > 0 and claim.is_pay_in_done):
                    claim.state = "completed"

    def validate_claim(self, res):
        """validation checks for the claims"""
        if res.claim_amount <= 0:
            raise UserError(_("Claim amount should be greater 0."))
        if res.is_advance_needed:
            if not res.advance_amount or res.advance_amount <= 0:
                raise UserError(_("a value greater than 0 is required as Advance Amount!."))
            if res.advance_amount and res.advance_amount > res.claim_amount:
                raise UserError(_("Advance Amount Cannot be greater than claim amount   ."))

    @api.depends("payment_ids")
    def _compute_count(self):
        """compute payment count"""
        for rec in self:
            rec.payment_count = len(rec.payment_ids)

    @api.depends('travel_exp_line_ids.total_amount', 'lodging_exp_line_ids.total_amount',
                 'boarding_exp_line_ids.total_amount', 'other_exp_line_ids.total_amount')
    def _compute_amount_to_pay(self):
        """compute the amount_to_pay:amount to pay to employee  if any or amount_to_pay_in:amount to collect form employee if any"""
        for rec in self:
            amount_to_pay = rec.total_amount - rec.advance_payed_amount
            rec.amount_to_pay = amount_to_pay if amount_to_pay > 0 else 0.00
            rec.amount_to_pay_in = abs(amount_to_pay) if amount_to_pay <= 0 else 0.00

    @api.model
    def create(self, vals):
        company_id = self.env.company.id
        sequence = self.env['ir.sequence'].search(
            [('company_id', '=', company_id), ('code', '=', 'hr.expense.claim.seq')])
        if not sequence:
            sequence = self.env['ir.sequence'].search([('code', '=', 'hr.expense.claim.seq')], limit=1)
            new_sequence = sequence.sudo().copy()
            new_sequence.company_id = company_id
            code = new_sequence.next_by_id()
        else:
            code = self.env['ir.sequence'].next_by_code('hr.expense.claim.seq')
        vals['name'] = code
        res = super().create(vals)
        self.validate_claim(res)
        return res

    def write(self, vals):
        expenses = {'travel_exp_line_ids': 'travel', 'lodging_exp_line_ids': 'lodging',
                    'boarding_exp_line_ids': 'boarding', 'other_exp_line_ids': 'other'}
        for expense, name in expenses.items():
            if vals.get(expense):
                if self.is_advance_needed and not self.is_advance_payed and self.state != 'approved_without_advance':
                    raise UserError(_("Please pay the advance before adding expense lines"))
                if self.sheet_id:
                    raise UserError(
                        _("Expense Sheet for the Expense Lines is already generated cannot add new expense in this claim, please submit the claim."))
                for sublist in vals.get(expense):
                    item  = sublist[-1]
                    if item:
                        amount = item.get('total_amount')
                        if not amount or amount <= 0:
                            raise UserError(
                                _(f"a value greater than 0 is required as Amount in {name.capitalize()} Expense line!."))
                        form_date = datetime.strptime(item.get('date_from'), '%Y-%m-%d').date() if item.get(
                            'date_from') else False
                        to_date = datetime.strptime(item.get('date_from'), '%Y-%m-%d').date() if item.get(
                            'date_to') else False
                        boarding_date = datetime.strptime(item.get('boarding_date'), '%Y-%m-%d').date() if item.get(
                            'boarding_date') else False
                        if form_date and form_date < self.expense_date:
                            raise UserError(
                                _(f"{name.capitalize()} Expense Date From should be after or same as Expense Date."))
                        if form_date and to_date and to_date < form_date:
                            raise UserError(
                                _(f"{name.capitalize()} Expense Date To should be after or same as From Date."))
                        if boarding_date and boarding_date < self.expense_date:
                            raise UserError(
                                _(f"{name.capitalize()} Expense {'Boarding' if name =='boarding' else ''} Date should be after or same as Expense Date."))
                        if self.claim_type == 'travel':
                            if not item.get('product_id'):
                                product = self.env['product.product'].search([('category_type', '=', name)],
                                                                             limit=1)
                                item['product_id'] = product.id
                        if not expense == 'other_exp_line_ids':
                            item['name'] = name + self.name
                        item['date'] = self.expense_date

        res = super(ExpenseClaim, self).write(vals)
        self.validate_claim(self)
        return res

    def action_claim_send_for_approval(self):
        """wizard action to set the claim for approval"""
        ctx = {'function': 'action_hr_expense_claim_send_for_approval'}
        if self.user_comment:
            ctx.update({'default_description': self.user_comment})
        form_view_id = self.env.ref('hr_expense_extended.hr_expense_claim_comment_form').id
        return {
            'name': _('Comments'),
            'view_type': 'form',
            'target': 'new',
            'context': ctx,
            "view_mode": 'form',
            'res_model': 'hr.expense.claim.comment',
            'type': 'ir.actions.act_window',
            'view_id': form_view_id
        }

    def action_mu_approval(self):
        """wizard action to mu approval"""
        ctx = {'function': 'action_hr_expense_claim_mu_approve'}
        form_view_id = self.env.ref('hr_expense_extended.hr_expense_claim_comment_form').id
        return {
            'name': _('Comments'),
            'view_type': 'form',
            'target': 'new',
            'context': ctx,
            "view_mode": 'form',
            'res_model': 'hr.expense.claim.comment',
            'type': 'ir.actions.act_window',
            'view_id': form_view_id
        }

    def action_finance_approval(self):
        """wizard action to finance approval"""
        ctx = {
            'function': 'action_hr_expense_claim_finance_approve' if not self.is_advance_needed else 'action_hr_expense_claim_finance_approve_advance'}
        form_view_id = self.env.ref('hr_expense_extended.hr_expense_claim_comment_form').id
        return {
            'name': _('Comments'),
            'view_type': 'form',
            'target': 'new',
            'context': ctx,
            "view_mode": 'form',
            'res_model': 'hr.expense.claim.comment',
            'type': 'ir.actions.act_window',
            'view_id': form_view_id
        }

    def action_reject(self):
        """wizard action to reject claim"""
        ctx = {'function': 'action_hr_expense_claim_rejected'}
        form_view_id = self.env.ref('hr_expense_extended.hr_expense_claim_comment_form').id
        return {
            'name': _('Comments'),
            'view_type': 'form',
            'target': 'new',
            'context': ctx,
            "view_mode": 'form',
            'res_model': 'hr.expense.claim.comment',
            'type': 'ir.actions.act_window',
            'view_id': form_view_id
        }

    def action_cancel(self):
        """wizard action to cancel"""
        ctx = {'function': 'action_hr_expense_claim_cancel'}
        form_view_id = self.env.ref('hr_expense_extended.hr_expense_claim_comment_form').id
        return {
            'name': _('Comments'),
            'view_type': 'form',
            'target': 'new',
            'context': ctx,
            "view_mode": 'form',
            'res_model': 'hr.expense.claim.comment',
            'type': 'ir.actions.act_window',
            'view_id': form_view_id
        }

    def action_submit_expenses(self):
        """action to submit expense"""
        expense = ('travel_exp_line_ids', 'lodging_exp_line_ids', 'boarding_exp_line_ids', 'other_exp_line_ids')
        lines = []
        for exp in expense:
            if self[exp]:
                lines.append(exp)
        if not lines:
            raise UserError(_("Please add at least one expense line before submitting"))
        expenses = self.travel_exp_line_ids + self.lodging_exp_line_ids + self.boarding_exp_line_ids + self.other_exp_line_ids
        if not any(expense.state != 'draft' or expense.sheet_id for expense in expenses):
            context_vals = expenses._get_default_expense_sheet_values()
            sheet = self.env['hr.expense.sheet'].create(context_vals)
        else:
            sheet = expenses.mapped('sheet_id')
        self.sheet_id = sheet.id
        sheet.action_submit_sheet()

    def action_view_sheet(self):
        self.ensure_one()
        form_view_id = self.env.ref('hr_expense_extended.view_claim_hr_expense_sheet_form').sudo().id
        return {
            'type': 'ir.actions.act_window',
            'view_id': form_view_id,
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'context': {'create': False, 'edit': False},
            'res_id': self.sudo().sheet_id.id
        }
    def approve_and_post_expense_sheets(self):
        """action to approve and post expense report"""
        approve = self.sheet_id.with_context({'model_from': 'hr.expense.claim'}).approve_expense_sheets()
        if approve:
            return approve
        self.sheet_id.action_sheet_move_create()
        if self.is_advance_payed:
            for payment in self.payment_ids:
                if not payment.move_id.has_reconciled_entries:
                    self.action_reconcile_payment(payment)

    def action_reconcile_payment(self, payment):
        """action to assign outstanding line and make this reconciled"""
        payments_outbound = self.payment_ids.filtered(
            lambda payment: payment.payment_type == 'outbound')
        move_lines = payment.line_ids.filtered(
            lambda line: line.account_type == 'liability_payable' and not line.reconciled)
        move = self.sheet_id.account_move_id if payment.payment_type == 'outbound' else payments_outbound.move_id
        move.js_assign_outstanding_line(move_lines.id)

    def action_view_payment(self):
        """action to view linked pyment"""
        for rec in self:
            return {
                'name': _('Payments'),
                'res_model': 'account.payment',
                'view_mode': 'list,form',
                'domain': [('claim_id', '=', rec.id)],
                'target': 'current',
                'context': {'create': False, 'from_claim': True, },
                'type': 'ir.actions.act_window',
            }

    def action_payment_wiz(self):
        """action to  call payment wizard"""
        payment_mode = self.env.context.get('default_payment_type')
        name = 'Register Payment'

        if self.env.context.get('expense_payout'):
            name = 'Register Payment'
        elif payment_mode == 'outbound':
            name = 'Advance Payment'
        elif payment_mode == 'inbound':
            name = 'Balance Collection'
        return {
            'name': _(name),
            'res_model': 'expense.claim.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
