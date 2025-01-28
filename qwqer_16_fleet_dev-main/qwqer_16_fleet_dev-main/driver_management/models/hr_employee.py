# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HrEmployee(models.Model):
    """
    Model contains modifications or driver management
    """
    _inherit = 'hr.employee'
    _description = 'Employee'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(HrEmployee, self).name_search(name, args, operator, limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search(['|', ('driver_uid', operator, name), ('name', operator, name)] + args, limit=limit)
            return recs.name_get()
        return res

    @api.onchange('address_id')
    def _onchange_address(self):
        self.work_phone = False
        self.mobile_phone = False

    @api.model
    def create(self, vals):
        res = super(HrEmployee, self).create(vals)
        # Call to employee creation method
        res.create_employee_partner()
        return res

    @api.onchange('user_id')
    def onchange_update_related_partner(self):
        for rec in self:
            if rec.user_id:
                rec.related_partner_id = rec.user_id.partner_id.id

    def create_employee_partner(self):
        for rec in self:
            # Fetch payable account once and reuse if needed
            payable_account = None
            if not rec.driver_uid:
                payable_account = self.env['account.account'].search([('is_expense_credit', '=', True)], limit=1)

            # Set payable account if necessary
            if payable_account:
                rec.related_partner_id.property_account_payable_id = payable_account.id

            # Fetch driver journal if needed
            if rec.driver_uid:
                driver_journal = self.env['account.journal'].search([('is_driver_journal', '=', True)], limit=1)
                if not rec.journal_id and driver_journal:
                    rec.journal_id = driver_journal.id
                if not rec.plan_detail_id and rec.region_id and rec.region_id.default_driver_payout_plan:
                    rec.update({'plan_detail_id': rec.region_id.default_driver_payout_plan.id,
                                'payout_type': 'week'
                                })
                # Link existing user or create a new one if necessary
            if rec.user_id:
                rec.related_partner_id = rec.user_id.partner_id.id

            elif rec.driver_uid and not rec.related_partner_id:
                partner_rec = self.env['res.partner'].create({
                    'display_name': rec.name,
                    'name': rec.name,
                    'email': rec.work_email,
                    'phone': rec.work_phone or rec.mobile_phone,
                    'region_id': rec.region_id.id,
                })
                rec.related_partner_id = partner_rec.id
            elif not rec.driver_uid and not rec.work_email:
                    raise ValidationError(_("Work Email are mandatory"))

            # Set partner account based on job if it's a driver account
            if rec.job_id.account_id.is_driver_account and rec.related_partner_id:
                rec.related_partner_id.property_account_receivable_id = rec.job_id.account_id.id
                rec.related_partner_id.property_account_payable_id = rec.job_id.account_id.id

            # Assign driver_uid if both related partner and driver_uid exist
            if rec.related_partner_id and rec.driver_uid:
                rec.related_partner_id.driver_uid = rec.driver_uid

    def action_set_account_for_related_partner(self):
        for rec in self:
            if rec.job_id.account_id.is_driver_account and rec.related_partner_id:
                rec.related_partner_id.property_account_receivable_id = rec.job_id.account_id.id
                rec.related_partner_id.property_account_payable_id = rec.job_id.account_id.id

    # Server action for "Update Related Partner Driver ID"
    def action_relate_partner_driver_uid(self):
        for rec in self:
            if rec.related_partner_id and rec.driver_uid:
                rec.related_partner_id.driver_uid = rec.driver_uid
                rec.related_partner_id.emp_id = rec.id

    def action_archive(self):
        res = super(HrEmployee, self).action_archive()
        user_ids = self.mapped('user_id')
        partner_ids = self.mapped('related_partner_id')

        if user_ids:
            user_ids.action_archive()
        if partner_ids:
            partner_ids.action_archive()
        return res

    def action_unarchive(self):
        res = super(HrEmployee, self).action_unarchive()
        user_ids = self.mapped('user_id')
        partner_ids = self.mapped('related_partner_id')

        if user_ids:
            user_ids.action_archive()
        if partner_ids:
            partner_ids.action_archive()
        return res

    def get_user_expense_approver(self):
        manager_group = self.env.ref('hr_expense.group_hr_expense_team_approver', raise_if_not_found=False)
        emp_rec = self.env['hr.employee'].search([('user_id', 'in', manager_group.users.ids)])
        return [('id', 'in', emp_rec.ids), ('driver_uid', '=', False), ('employee_status', '=', 'active')]

    #TODO @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(HrEmployee, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                   submenu=submenu)
    #     doc = etree.XML(res['arch'])
    #     if self._context.get('driver_only', False):
    #         if view_type == 'tree':
    #             for node_form in doc.xpath("//tree"):
    #                 node_form.set("create", 'false')
    #             for node_form in doc.xpath("//tree"):
    #                 node_form.set("delete", 'false')
    #     if self._context.get('employee_edit', False) and not self._context.get('driver_employee',
    #                                                                            False) and not self.env.user.has_group(
    #             'zb_qwqer_hr_customization.group_for_create_edit_employee'):
    #         if view_type == 'form' or view_type == "tree":
    #             for node_form in doc.xpath("//tree"):
    #                 node_form.set("create", 'false')
    #             for node_form in doc.xpath("//form"):
    #                 node_form.set("create", 'false')
    #             for node_form in doc.xpath("//form"):
    #                 node_form.set("edit", 'false')
    #     res['arch'] = etree.tostring(doc)
    #     return res

    #TODO @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     result = super(HrEmployeeInherit, self).fields_view_get(view_id=view_id, view_type=view_type,
    #                                                             toolbar=toolbar,
    #                                                             submenu=submenu)
    #     doc = etree.XML(result['arch'])
    #     if view_type == 'form' and self.env.user.has_group('zb_qwqer_user_access.auditor_menu_access_group'):
    #         for node_form in doc.xpath("//form"):
    #             node_form.set("create", 'false')
    #             node_form.set("edit", 'false')
    #             node_form.set("delete", 'false')
    #     if view_type == 'tree' and self.env.user.has_group('zb_qwqer_user_access.auditor_menu_access_group'):
    #         for node_form in doc.xpath("//tree"):
    #             node_form.set("create", 'false')
    #             node_form.set("edit", 'false')
    #             node_form.set("delete", 'false')
    #
    #     result['arch'] = etree.tostring(doc, encoding='unicode')
    #     return result

    is_driver = fields.Boolean(string='Is Driver', default=False, copy=False)
    cashfree_payment = fields.Boolean(string='Payment via Cashfree')
    driver_uid = fields.Char(string='Driver ID', index=True, copy=False)  # V13_field: driver_id
    employee_uid = fields.Char(string='Employee ID', index=True)  # V13_field: employee_id
    employee_status = fields.Selection([('active', 'Active'),
                                        ('inactive', 'Inactive')], string='Employee Status')
    join_date = fields.Date(string="Joining Date", copy=False)
    relive_date = fields.Date(string="Reliving Date", copy=False)
    journal_id = fields.Many2one("account.journal", string='Journal')
    related_partner_id = fields.Many2one("res.partner",string="Related Partner")
    claim_limit = fields.Integer(string='Claim Limit', copy=False)
    driver_category = fields.Selection([('live', 'Live'), ('dedicated', 'Dedicated')], string='Driver Category')
    is_dedicated_orders = fields.Boolean(string='Dedicated orders only', copy=False)
    employee_reporting_pin_code = fields.Char(string = "Reporting Pincode")
    employee_reporting_location = fields.Char(string = "Reporting Location")
    employee_referred_by = fields.Char(string = "Referred By", copy=False)
    employee_vendor_name = fields.Char(string = "Vendor Name")
    shift_type_id = fields.Many2one('hr.employee.shift.type', string="Shift Type")
    blocked_reason = fields.Char(string = "Blocked Reason")

    # Private Contact
    emp_address = fields.Text(string = "Employee Address")
    aadhar_number = fields.Char(string='Aadhar Number')
    uan = fields.Char(string="UAN No")
    epf_no = fields.Char(string="EPF No")
    esi_no = fields.Char(string='ESI IP No')
    # home_work_distance = fields.Integer(string='Home Work Distance')  # V13_field: km_home_work

    # Family Status
    nominee = fields.Char(string='Nominee', copy=False)
    nominee_relation = fields.Char(string='Nominee Relationship', copy=False)
    employee_nominee_dob = fields.Date(string = "Nominee DOB", copy=False)

    # Education
    educational_certificate = fields.Binary(string="Certificate")

    # Citizenship
    blood_group = fields.Char(string='Blood Group')

    # payout detail
    plan_detail_id = fields.Many2one('driver.payout.plans', string="Plan", tracking=True)
    payout_type = fields.Selection([
            ('week', 'Weekly'),
            ('month', 'Monthly'),
            ], string='Payout Type', tracking=True)
    vehicle_no = fields.Char(string='Vehicle Number')
    vehicle_type = fields.Char(string='Vehicle Type')
    vehicle_category_id = fields.Many2one('driver.vehicle.category', string='Vehicle Category')
    vehicle_attachment_ids = fields.One2many('driver.vehicle.documents', 'emp_id',
                                             string='Vehicle Documents', order='name')
    dedicated_customer_ids = fields.One2many('res.partner','emp_id',string='Dedicated Customer')
    employee_type = fields.Selection(selection_add=[('driver', 'Driver'), ('sales_person', 'Sales Person')],
                                     ondelete={'driver': 'set default', 'sales_person': 'set default'})
    # Payment to vendor
    driver_partner_id = fields.Many2one('res.partner', string='Vendor')
    vendor_beneficiary = fields.Char(string="Vendor Beneficiary ID")
    vendor_account_no = fields.Char(string='Vendor Account Number')
    vendor_ifsc_code = fields.Char(string='Vendor IFSC Code')
    vendor_pan_no = fields.Char(string='Vendor PAN No')
    vendor_tds_tax_id = fields.Many2one('account.tax',string='Driver TDS Tax')

    # expense manager employee addition
    expense_manager_emp_id = fields.Many2one('hr.employee', string="Expense Manager", domain=get_user_expense_approver)

    # employee documents
    emp_docs_ids = fields.One2many('hr.employee.documents', 'emp_id',
                                   string='Employee Documents')
    # employee assets
    emp_asset_ids = fields.One2many('employee.assets', 'emp_id',
                                   string='Employee Assets')
    # employee insurance
    emp_insurance_ids = fields.One2many('employee.insurance.policy', 'emp_id',
                                   string='Employee Insurance')

    _sql_constraints = [
        ('code_unique', 'unique (driver_uid)', "Driver ID already exists!"),
        ('employee_id_unique', 'unique (employee_id)', "Employee ID Card Number already exists!"),
    ]

    def write(self, vals):
        if vals.get('region_id') and self.driver_uid and not vals.get('plan_detail_id') and not vals.get('payout_type'):
            new_region = self.env['sales.region'].browse(vals.get('region_id'))
            if new_region.default_driver_payout_plan:
                vals.update({'plan_detail_id': new_region.default_driver_payout_plan.id, 'payout_type': 'week'})
            else:
                vals.update({'plan_detail_id': None, 'payout_type': None})
        res = super(HrEmployee, self).write(vals)
        for rec in self:
            if not rec.driver_uid:
                if vals.get('work_email'):
                    if rec.related_partner_id:
                        rec.related_partner_id.email = vals.get('work_email')
                    if rec.user_id:
                        rec.user_id.login = vals.get('work_email')
        return res

    @api.onchange('region_id')
    def onchange_region_id(self):
        for rec in self:
            # Early exit if region_id or driver_uid is not set
            if not rec.region_id or not rec.driver_uid:
                continue
            vals = {'department_id': False, 'parent_id': False}
            # Search for region manager details only if region_id is present
            # data_id = self.env['region.manager'].sudo().search([('region_id', '=', rec.region_id.id)], limit=1)
            #TODO if data_id:
            #     vals.update({
            #         'department_id': data_id.department_id.id,
            #         'parent_id': data_id.employee_id.id
            #     })
            # Check for 'driver_employee' in context and update payout plan details
            if self.env.context.get('default_is_driver'):
                payout_plan = rec.region_id.default_driver_payout_plan
                vals.update({
                    'plan_detail_id': payout_plan.id if payout_plan else False,
                    'payout_type': 'week' if payout_plan else False
                })
            rec.update(vals)

    @api.onchange('is_under_vendor', 'driver_partner_id')
    def onchange_driver_partner(self):
        for rec in self:
            if rec.is_under_vendor and rec.driver_partner_id:
                missing_fields = []
                if not rec.driver_partner_id.account_no:
                    missing_fields.append(_('Account Number'))
                if not rec.driver_partner_id.ifsc_code:
                    missing_fields.append(_('IFSC Code'))
                if not rec.driver_partner_id.l10n_in_pan:
                    missing_fields.append(_('PAN Number'))
                if not rec.driver_partner_id.tax_tds_id:
                    missing_fields.append(_('TDS Tax'))
                if not rec.driver_partner_id.beneficiary:
                    missing_fields.append(_('Beneficiary in Cashfree'))
                if missing_fields:
                    raise ValidationError(
                        _("The following fields are not set for the Vendor: %s") % ', '.join(missing_fields)
                    )
                rec.vendor_account_no = rec.driver_partner_id.account_no if rec.driver_partner_id.account_no else ''
                rec.vendor_beneficiary = rec.driver_partner_id.beneficiary if rec.driver_partner_id.beneficiary else ''
                rec.vendor_ifsc_code = rec.driver_partner_id.ifsc_code if rec.driver_partner_id.ifsc_code else ''
                rec.vendor_pan_no = rec.driver_partner_id.l10n_in_pan if rec.driver_partner_id.l10n_in_pan else ''
                rec.vendor_tds_tax_id = rec.driver_partner_id.tax_tds_id if rec.driver_partner_id.tax_tds_id else ''
            elif not rec.is_under_vendor:
                rec.write({
                    'driver_partner_id': False,
                    'vendor_account_no': '',
                    'vendor_beneficiary': '',
                    'vendor_ifsc_code': '',
                    'vendor_pan_no': '',
                    'vendor_tds_tax_id': '',
                })