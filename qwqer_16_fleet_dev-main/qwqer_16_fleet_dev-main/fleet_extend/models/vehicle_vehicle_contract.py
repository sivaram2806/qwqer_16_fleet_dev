# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import timedelta, datetime, date


class VehicleContractType(models.Model):
    """
    This model contains information about different types of contract,
    #V13_model name:  configure.contract.type
    """
    _name = "vehicle.contract.type"
    _description = "Vehicle Contract Type"

    name = fields.Char(string="Contract Type", required=True)
    code = fields.Char(string="Code", required=True)
    company_id = fields.Many2one(comodel_name='res.company', string="Company", required=True, readonly=True,
                                 default=lambda self: self.env.company)


class VehicleContractCategory(models.Model):
    """
    This model contains information about different categories of contract,
    #V13_model name: configure.contract.name
    """
    _name = "vehicle.contract.category"
    _description = "Vehicle Contract Category"

    name = fields.Char(string="Contract Category Name", required=True)
    code = fields.Char(string="Contract Code", required=True)
    short_code = fields.Char(string="Contract Short Code", required=True)
    company_id = fields.Many2one(comodel_name='res.company', string="Company", required=True, readonly=True,
                                 default=lambda self: self.env.company)
    contract_classification = fields.Selection(
        selection=[("others", "others"), ("ftl", "FTL")],
        string="Contract Classification")

    _sql_constraints = [
        ('contract_name_unique', 'unique (name,company_id)',
         'The Contract Name must be unique !'),
        ('contract_code_unique', 'unique (code,company_id)',
         'The Contract Code must be unique !')
    ]

    @api.onchange('name')
    def _onchange_short_code(self):
        """Automatically create short code for vehicle contract category"""
        for rec in self:
            if rec.name:
                rec.short_code = rec.name[:3].upper() if len(rec.name) >= 3 else (rec.name[0] * 3).upper()
            else:
                rec.short_code = False


class VehicleVehicleContract(models.Model):
    """
    This model contains record of vehicle, #V13_model name: contract.management
    """
    _name = 'vehicle.contract'
    _description = 'Vehicle Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'contract_num'
    _order = 'id desc'

    contract_num = fields.Char(string="Contract Number", copy=False)
    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer')
    contract_cat_id = fields.Many2one(
        comodel_name='vehicle.contract.category',
        string='Contract Category')  # V13_field: contract_name_id, model: 'configure.contract.name'
    contract_classification = fields.Selection(selection=[("others", "others"), ("ftl", "FTL")],
                                               string="Contract Classification", required=True,
                                               related='contract_cat_id.contract_classification')
    contract_type_id = fields.Many2one(comodel_name='vehicle.contract.type',
                                       string="Contract Type")  # field: contract_type_id, model: 'configure.contract.type'
    region_id = fields.Many2one(comodel_name='sales.region',
                                string="Region",
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")  # V13_field: region_id, model: 'region'
    type = fields.Selection(selection=[
        ("product", "Product"),
        ("service", "Service")], string="Type")
    start_date = fields.Date(string="Start Date", copy=False)
    end_date = fields.Date(string="End Date", copy=False)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id)
    cost = fields.Monetary(string="Cost")
    quantity = fields.Integer(string="Quantity")
    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term', string="payment terms")
    note = fields.Text(string="Description", copy=False)
    approval_stage = fields.Selection(selection=[
        ('new', 'New'),
        ('send_for_approval', 'Send for Approval'),
        ('mu_head_approved', 'Reporting Manager Approved'),
        ('finance_approved', 'Finance Approved')],
        default="new", string="Stage", tracking=True, copy=False)  # V13_field: stage, model: 'configure.contract.type'
    state = fields.Selection(selection=[
        ("new", "New"),
        ("running", "Running"),
        ("expired", "Expired"),
        ("closed", "Closed")],
        default="new", string="State", tracking=True, group_expand='read_group_stage_ids', copy=False)
    agreement = fields.Binary(string="Agreement", copy=False)
    comments = fields.Text(string="Comments", copy=False)
    attachment_ids = fields.One2many(comodel_name='contract.attachments',
                                     inverse_name='contract_id',
                                     copy=False)  # V13_field: agrmnt_attchmnt_line_ids, model: 'agreement.attachment'
    company_id = fields.Many2one(comodel_name='res.company', string="Company", required=True, readonly=True,
                                 default=lambda self: self.env.company)
    is_editable = fields.Boolean(compute='_compute_is_editable', default=True)
    parent_id = fields.Many2one(comodel_name='vehicle.contract', string="Parent Contract")
    to_renew = fields.Boolean(string='To Renew', default=False)
    child_ids = fields.One2many('vehicle.contract', 'parent_id', copy=False)
    child_count = fields.Char(string="Child Contract Count", compute='_compute_child_count')
    user_action_history_ids = fields.One2many(comodel_name='vehicle.contract.action.history',
                                              inverse_name='vehicle_contract_id',
                                              string='User Action History')
    is_document_editable = fields.Boolean(string="Allow document editing",
                                          compute='_compute_is_document_editable')
    agreement_name = fields.Char(string='Agreement Name')

    _sql_constraints = [('cost_greater_than_zero', 'CHECK(cost > 0)', 'Contract amount should be greater than zero!'),
                        ('quantity_greater_than_zero', 'CHECK(quantity > 0)', 'Contract quantity should be greater '
                                                                              'than zero!'),
                        ('end_date_check', 'CHECK(end_date > start_date)', 'End date should be greater than '
                                                                           'start date!'), ]

    @api.constrains('end_date')
    def _check_end_date(self):
        for rec in self:
            if rec.end_date <= fields.Date.today():
                raise UserError("End date should be less than or equal to today.")

    @api.model_create_multi
    def create(self, vals_list):  # child, parent for expired records
        for vals in vals_list:
            rec = super().create(vals)
            company_id = self.env.company.id
            if not rec.contract_num:
                prefix = str(rec.contract_cat_id.short_code if rec.contract_classification == 'others' else 'FTL')
                sequence = self.env['ir.sequence'].search(
                    [('company_id', '=', company_id), ('code', '=', 'vehicle.contract.seq')])
                if not sequence:
                    sequence = self.env['ir.sequence'].search([('code', '=', 'vehicle.contract.seq')], limit=1)
                    new_sequence = sequence.sudo().copy()
                    new_sequence.company_id = company_id
                    code = new_sequence.next_by_id()
                else:
                    code = self.env['ir.sequence'].next_by_code('vehicle.contract.seq')
                rec.contract_num = str(prefix + code)
                return rec
            else:
                return rec

    def write(self, vals):  # does the user have permissions to change other fields in stages
        approval_stage = vals.get('approval_stage')
        if approval_stage:
            stage_to_group = {
                'send_for_approval': 'fleet_extend.fleet_group_vehicle_contract_user',
                'finance_approved': 'fleet_extend.fleet_group_vehicle_contract_finance_manager',
                'mu_head_approved': 'fleet_extend.fleet_group_vehicle_contract_mu_manager'
            }
            required_group = stage_to_group.get(approval_stage)
            if required_group and not self.env.user.has_group(required_group):
                raise UserError(_("You don't have permission to change the stage. Please refresh the page!"))
        if vals.get('start_date'):
            parent = self.search([('child_ids', '=', self.id)])
            if parent and parent.state == 'running':
                child_start_date = (datetime.strptime(vals.get('start_date'), "%Y-%m-%d")).date()
                if parent.end_date >= child_start_date:
                    raise UserError(
                        _(f'Start date should not be set as date before or equal to the Parent contract {parent.contract_num} end date!')
                    )
        return super().write(vals)

    @api.model
    def read_group_stage_ids(self, states, domain, order):
        return ['new', 'running', 'expired', 'closed']

    def _compute_child_count(self):
        for rec in self:
            rec.child_count = len(rec.child_ids)

    def button_show_child_contracts(self):
        return {
            'name': 'Contracts',
            'domain': [('parent_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'vehicle.contract',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': {
                "create": False
            }
        }

    def _compute_is_editable(self):
        is_admin = self.env.user.has_group('fleet_extend.fleet_group_vehicle_contract_user_admin_user')
        if self.approval_stage == 'new':
            is_user = self.env.user.has_group('fleet_extend.fleet_group_vehicle_contract_user')
            self.is_editable = is_admin or (self.env.user == self.create_uid and is_user)
        elif self.approval_stage == 'send_for_approval':
            is_mu_manager = self.env.user.has_group('fleet_extend.fleet_group_vehicle_contract_mu_manager')
            self.is_editable = is_admin or is_mu_manager
        elif self.approval_stage == 'mu_head_approved':
            is_finance_manager = self.env.user.has_group('fleet_extend.fleet_group_vehicle_contract_finance_manager')
            self.is_editable = is_admin or is_finance_manager
        else:
            self.is_editable = False

    def action_sent_for_approval(self):
        for rec in self:
            ctx = {'function': 'action_sent_for_approval_comment'}
            if not rec.agreement:
                raise UserError(_("Attach agreement before sending for approval"))
            form_view_id = rec.env.ref('fleet_extend.vehicle_contract_action_history_wizard_form').id
            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'vehicle.contract.action.history.wizard',
                'type': 'ir.actions.act_window',
                'view_id': form_view_id
            }

    def action_return(self):
        for rec in self:
            if rec.approval_stage in ['mu_head_approved', 'send_for_approval']:
                functions = {
                    'mu_head_approved': 'action_return_to_send_for_approval',
                    'send_for_approval': 'action_return_to_new'
                }
                ctx = {'function': functions[rec.approval_stage]}
                form_view_id = rec.env.ref('fleet_extend.vehicle_contract_action_history_wizard_form').id
                return {
                    'name': _('Comments'),
                    'view_type': 'form',
                    'target': 'new',
                    'context': ctx,
                    'view_mode': 'form',
                    'res_model': 'vehicle.contract.action.history.wizard',
                    'type': 'ir.actions.act_window',
                    'view_id': form_view_id
                }

    def action_mu_approve(self):
        for rec in self:
            ctx = {'function': 'action_mu_approve_comment'}
            form_view_id = rec.env.ref('fleet_extend.vehicle_contract_action_history_wizard_form').id
            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'vehicle.contract.action.history.wizard',
                'type': 'ir.actions.act_window',
                'view_id': form_view_id
            }

    def action_finance_approve(self):
        for rec in self:
            ctx = {'function': 'action_finance_approve_comment'}
            form_view_id = rec.env.ref('fleet_extend.vehicle_contract_action_history_wizard_form').id
            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'vehicle.contract.action.history.wizard',
                'type': 'ir.actions.act_window',
                'view_id': form_view_id
            }

    def action_close_contract(self):
        for rec in self:
            ctx = {'function': 'action_close_contract_comment'}
            form_view_id = rec.env.ref('fleet_extend.vehicle_contract_action_history_wizard_form').id
            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'vehicle.contract.action.history.wizard',
                'type': 'ir.actions.act_window',
                'view_id': form_view_id
            }

    def manage_contract_expiry(self):
        """
        Check if contract is about to expire and handle expired contracts.
        """
        # Get the delay alert parameter
        delay_alert_contract = int(
            self.env['ir.config_parameter'].sudo().get_param('hr_fleet.delay_alert_contract', default=30)
        )

        last_date = date.today() + timedelta(days=delay_alert_contract)
        today = date.today()

        # Search for contracts to renew and those that are expired
        contracts = self.env['vehicle.contract'].search([('state', 'in', ['new', 'running']),
                                                         ('approval_stage', '=', 'finance_approved')])
        to_renew_list = []
        expired_list = []
        new_contract_list = []
        for contract in contracts:
            if contract.end_date:
                if contract.end_date < last_date and not contract.to_renew:
                    to_renew_list.append(contract)
                elif contract.end_date <= today:
                    expired_list.append(contract)
            if contract.state == 'new' and contract.start_date <= today and not contract.child_ids and not contract \
                    .parent_id:
                new_contract_list.append(contract)

        # Set to_renew to True and send alert emails
        if to_renew_list:
            for contract in to_renew_list:
                contract.to_renew = True
                email_values = {
                    'subject': f'Contract {contract.contract_num} Expiring Soon',
                    'body_content': f'Expire within {delay_alert_contract} days',
                    'from_expire': True
                }
                template_id = self.env.ref('fleet_extend.expiring_ftl_contract_email_template')
                template_id.with_context(email_values).send_mail(contract.id, email_values=None, force_send=True)

        # Handle expired contracts
        if expired_list:
            for contract in expired_list:
                contract.write({'state': 'expired', 'to_renew': False})
                child_contract = self.env['vehicle.contract'].search(
                    [('parent_id', '=', contract.id)], limit=1, order='id desc'
                )
                if child_contract and child_contract.approval_stage == 'finance_approved':
                    child_contract.write({'state': 'running'})
                    email_values = {
                        'body_content': f'Contract {contract.contract_num} has been expired',
                        'child_contract': child_contract.contract_num,
                        'from_expire': True
                    }
                    template_id = self.env.ref('fleet_extend.running_ftl_contract_email_template')
                    template_id.with_context(email_values).send_mail(child_contract.id, email_values=None,
                                                                     force_send=True)
                else:
                    email_values = {
                        'subject': f'Contract {contract.contract_num} Expired',
                        'body_content': 'been Expired',
                        'from_expire': True
                    }
                    template_id = self.env.ref('fleet_extend.expiring_ftl_contract_email_template')
                    template_id.with_context(email_values).send_mail(contract.id, email_values=None, force_send=True)

        # Handle newly created contracts
        if new_contract_list:
            for contract in new_contract_list:
                if contract.start_date <= fields.Date.today():
                    contract.write({'state': 'running'})
                    email_values = {
                        'subject': f'Contract {contract.contract_num} moved to Running',
                        'body_content': 'moved to Running',
                        'from_expire': True
                    }
                    template_id = self.env.ref('fleet_extend.expiring_ftl_contract_email_template')
                    template_id.with_context(email_values).send_mail(contract.id, email_values=None, force_send=True)

    def increment_contract_num(self, input_string):
        if '/' in input_string:
            parts = input_string.split('/')
            numeric_value = int(parts[1]) + 1
            result = f"{parts[0]}/{numeric_value}"
        else:
            result = f"{input_string}/1"

        return result

    def action_renew_contract(self):
        child_id = self.env['vehicle.contract'].search([('parent_id', '=', self.id)], limit=1, order='id desc')
        new_contract_num = self.increment_contract_num(
            child_id.contract_num) if child_id else self.increment_contract_num(self.contract_num)
        new_contract_id = self.env['vehicle.contract'].create({
            'contract_num': new_contract_num,
            'customer_id': self.customer_id.id,
            'contract_cat_id': self.contract_cat_id.id,
            'contract_classification': self.contract_classification,
            'contract_type_id': self.contract_type_id.id,
            'region_id': self.region_id.id,
            'type': self.type,
            'currency_id': self.currency_id.id,
            'cost': self.cost,
            'quantity': self.quantity,
            'payment_term_id': self.payment_term_id.id,
            'note': self.note,
            'approval_stage': 'new',
            'state': 'new',
            'company_id': self.company_id.id,
            'parent_id': self.parent_id.id or self.id,
        })
        self.child_ids = [(4, new_contract_id.id)]
        template_id = self.env.ref('fleet_extend.renew_ftl_contract_email_template')
        email_values = {'child_contract': new_contract_id.contract_num, 'from_renew': True}
        template_id.with_context(email_values).send_mail(self.id, email_values=None, force_send=True)
        return {
            'name': 'New Contract',
            'type': 'ir.actions.act_window',
            'res_model': 'vehicle.contract',
            'view_mode': 'form',
            'res_id': new_contract_id.id
        }

    def action_run_contract(self):
        for rec in self:
            ctx = {'function': 'action_run'}
            form_view_id = rec.env.ref('fleet_extend.vehicle_contract_action_history_wizard_form').id
            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'vehicle.contract.action.history.wizard',
                'type': 'ir.actions.act_window',
                'view_id': form_view_id
            }

    def _compute_is_document_editable(self):
        self.is_document_editable = False
        if self.approval_stage == 'finance_approved' and self.state in ['new', 'running']:
            if self.env.user.has_group(
                    'fleet_extend.fleet_group_vehicle_contract_user_admin_user') or self.env.user.has_group(
                'fleet_extend.fleet_group_vehicle_contract_finance_manager'):
                self.is_document_editable = True
            else:
                self.is_document_editable = False

    def get_email_to(self):
        """ get email to"""
        joined_string = ""
        for record in self:
            group_obj = False
            emails = []
            if not self.env.context.get('from_run', False) and not self.env.context.get('from_expire', False):
                emails = [self.env.user.partner_id.email or '']

            if record.create_uid.partner_id.email not in emails and not self.env.context.get('from_return', False):
                emails.append(record.create_uid.partner_id.email or '')

            if self.env.context.get('from_send_for_approval', False):
                group_obj = self.env.ref('fleet_extend.fleet_group_vehicle_contract_mu_manager')

            elif self.env.context.get('from_mu_approve', False):
                group_obj = self.env.ref('fleet_extend.fleet_group_vehicle_contract_finance_manager')

            elif self.env.context.get('from_return', False) or self.env.context.get('from_finance_approve', False):
                user_action = self.env['vehicle.contract.action.history'].search(
                    [('vehicle_contract_id', '=', record.id)], limit=1, order='id desc')
                if user_action and user_action.action == 'MU Approved' and user_action.user_id.partner_id.email not in emails:
                    emails.append(user_action.user_id.partner_id.email or '')

            elif self.env.context.get('from_close', False) or self.env.context.get('from_renew',
                                                                                   False) or self.env.context.get(
                    'from_expire', False) or self.env.context.get('from_run', False):
                mu_user_action = self.env['vehicle.contract.action.history'].search(
                    [('vehicle_contract_id', '=', record.id), ('action', '=', 'MU Approved')], limit=1, order='id desc')
                finance_user_action = self.env['vehicle.contract.action.history'].search(
                    [('vehicle_contract_id', '=', record.id), ('action', '=', 'Finance Approved')], limit=1,
                    order='id desc')
                if mu_user_action and mu_user_action.user_id.partner_id.email not in emails:
                    emails.append(mu_user_action.user_id.partner_id.email or '')
                if finance_user_action and finance_user_action.user_id.partner_id.email not in emails:
                    emails.append(finance_user_action.user_id.partner_id.email or '')

            if group_obj:
                for user in group_obj.users:
                    if user.partner_id.email not in emails and (self.env.context.get('from_mu_approve',
                                                                                     False) or record.region_id.sale_zone_id in user.substate_id):
                        emails.append(user.partner_id.email or '')
            if emails:
                joined_string = ",".join(emails)
        return joined_string

    def unlink(self):
        if not self.env.user.has_group('fleet.fleet_group_manager'):
            raise UserError(_("You are not allowed to delete the trip."))

        non_deletable_states = [rec.approval_stage for rec in self if rec.approval_stage != 'new']
        if non_deletable_states:
            raise UserError(_("You cannot delete the trip when it is not in 'new' or 'rejected' state."))

        return super(VehicleVehicleContract, self).unlink()
