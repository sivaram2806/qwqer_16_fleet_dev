import re
from datetime import datetime
from operator import index

from odoo import fields, models, api, _
from odoo.api import model, _logger
from odoo.exceptions import ValidationError, UserError, AccessError
from odoo import SUPERUSER_ID


class CustomerOnboard(models.Model):
    """capturing the customer data"""
    _name = "customer.onboard"
    _description = "Customer Onboarding "
    _rec_name = 'customer_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_employee_id(self):
        user = self.env.user.id
        employee_id = self.env['hr.employee'].search([('user_id', '=', user),('company_id','=',self.env.company.id)])
        if employee_id:
            return employee_id.id

    def _get_service_type_id(self):
        service_type_id = self.env['partner.service.type'].search(
            [('is_fleet_service', '=', True), ('is_customer', '=', True)], limit=1)
        if service_type_id:
            return service_type_id.id

    customer_name = fields.Char(string='Customer Name', required=1)
    brand_name = fields.Char()
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    customer_status = fields.Selection(selection=[('new_customer', 'New Merchant'),
                                                  ('existing_customer', 'New Sub Merchant')],
                                       string="Customer Status", default='new_customer')
    is_a_sub_customer = fields.Boolean(string="Is a Sub Customer")
    parent_partner_id = fields.Many2one(comodel_name='res.partner', string="Parent Merchant")
    merchant_phone_number = fields.Char("Merchant Phone Number")
    submerchant_billing = fields.Selection(selection=[('sub_merchant', 'Sub-Merchant'),
                                                      ('main_merchant', 'Main-Merchant')],
                                           string="Sub-Merchant Billing", default='sub_merchant')

    source_id = fields.Many2one(comodel_name='utm.source', string='Source/Lead Type', required=1)
    customer_service_type_id = fields.Many2one(comodel_name='partner.service.type', string='Service Type',
                                               tracking=True,
                                               required=1, default=lambda self: self._get_service_type_id())
    customer_segment_id = fields.Many2one(comodel_name='partner.segment', string='Customer Segment', tracking=True)
    customer_type = fields.Selection(selection=[('b2c', 'B2C'), ('b2b', 'B2B')], string='Customer Type', default='b2b',
                                     required=1)
    industry_id = fields.Many2one(comodel_name='res.partner.industry', string='Customer Industry')
    region_id = fields.Many2one(comodel_name='sales.region', string='Region', required=1, domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    reporting_mu_id = fields.Many2one(comodel_name='hr.employee', string='Unit Head')
    payment_mode_ids = fields.Many2many(comodel_name='payment.mode', string='Payment Mode')
    merchant_amount_collection = fields.Selection(selection=[('yes', 'Yes'),
                                                             ('no', 'No')],
                                                  string="Merchant Amount Collection", default='no')
    # is_credit_bool = fields.Boolean(string="Is Credit", compute='_compute_is_credit_bool', store=True)
    amount_collection_limit = fields.Float(string="Amount Collection Limit")
    amount_collection_sign = fields.Char(string="Amount Collection Sign", default="Rs")
    settlement_time_id = fields.Many2one(comodel_name='settlement.time', string='Settlement Time')
    collection_charges = fields.Float(string="Collection Charges")
    collection_charges_sign = fields.Char(string="Collection Charges Sign", default="%")
    item_category_id = fields.Many2one(comodel_name="item.category", string="Item Category")
    gstin_number = fields.Char(string="GSTIN", tracking=True)
    tax_id = fields.Char(string='PAN')
    state = fields.Selection(selection=[('draft', 'Draft'), ('mu_approvals', 'Unit Head Approval'),
                                        ('finance_approvals', 'Under Finance Approval'),
                                        ('under_pricing_config', 'Under Pricing Configuration'),
                                        ('configurations_completed', 'Configurations Completed'),
                                        ('rejected', 'Rejected')

                                        ], string="Qualification Status", default='draft',
                             group_expand='_group_expand_states', tracking=True)
    followup_status_id = fields.Many2one(comodel_name="mail.activity.type", string="Follow-up Status", required=1)
    potential_orders_id = fields.Many2one(comodel_name='potential.orders', string="Potential Orders", copy=False)
    pricing_type = fields.Selection(selection=[('default', 'Default Pricing'),
                                               ('special', 'Special Pricing')],
                                    string="Pricing Type", default='special')
    product_line_id = fields.Many2one(comodel_name="product.lines", string="Product Lines")
    source_type_id = fields.Many2one(comodel_name="source.type", string="Order Placement")
    invoice_frequency_id = fields.Many2one(comodel_name='invoice.frequency', string='Customer Invoice Frequency')
    distance_limitation = fields.Float(string="Distance Limitation", copy=False)
    product_storage = fields.Selection(selection=[('yes', 'Yes'),
                                                  ('no', 'No')],
                                       string="Product Storage", default='no', copy=False)
    product_sorting = fields.Selection(selection=[('yes', 'Yes'),
                                                  ('no', 'No')],
                                       string="Product Sorting", default='no', copy=False)
    pick_up_area = fields.Text(string="Pick up Area")
    customer_email = fields.Char()
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char(string='Zip', change_default=True)
    city = fields.Char('City')
    state_id = fields.Many2one(comodel_name="res.country.state", string='State',domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one(comodel_name='res.country', string='Country',default=lambda self: self.env.company.country_id)
    contact_partner_id = fields.Many2one(comodel_name='res.partner', string='Contact', ondelete='restrict')
    lang_id = fields.Many2one(comodel_name='res.lang', string='Language', help="Language of the lead.")

    sales_person_id = fields.Many2one(comodel_name='hr.employee', string="Sales Person",
                                      default=lambda self: self._get_employee_id(), tracking=True)
    user_id = fields.Many2one(comodel_name='res.users', string='User')
    contact_name = fields.Char(string='Contact Name', tracking=30, required=1)
    phone_code = fields.Char(string="Code", default="+91")
    phone = fields.Char(string='Phone', tracking=50, required=1, index=True, copy=False)
    delivery_type_id = fields.Many2one(comodel_name='delivery.type', string='Type of Delivery')

    expected_revenue = fields.Float("Expected Revenue per Month")

    date_deadline = fields.Date(string='Expected Closing',
                                help="Estimate of the date on which the opportunity will be won.")
    lead_generated_by = fields.Many2one(comodel_name="res.users", string="Lead Generated By",
                                        default=lambda self: self.env.user)
    last_updated_on = fields.Datetime(string="Last Updated on")
    user_comment = fields.Text('Comments')
    user_comments_ids = fields.One2many('user.comments', 'comment_customer_onboard_id', string='User Comments')
    comments = fields.Text('Comments')
    user_action_ids = fields.One2many(comodel_name='onboard.user.action.history',
                                      inverse_name='action_customer_onboard_id',
                                      string='User Action History')

    lost_reason_comment = fields.Text('Comments')
    mu_pricing_plan_status = fields.Selection(selection=[('approved', 'Approved'),
                                                         ('rejected', 'Rejected')],
                                              string="Pricing Plan")
    mu_agreement_status = fields.Selection(selection=[('approved', 'Approved'),
                                                      ('rejected', 'Rejected')],
                                           string="Agreement")
    mu_payment_option_status = fields.Selection(selection=[('approved', 'Approved'),
                                                           ('rejected', 'Rejected')],
                                                string="Payment Mode")
    pricing_configuration = fields.Selection(selection=[('yes', 'Yes'),
                                                        ('no', 'No')],
                                             string="Pricing Configuration")
    b2b_merchant_creation = fields.Selection(selection=[('yes', 'Yes'),
                                                        ('no', 'No')],
                                             string="B2B Merchant Creation")
    mu_rejected_true = fields.Boolean(string="MU Rejected status", default=False)
    preferred_slot = fields.Selection(selection=[('early_morning', 'Early Morning'),
                                                 ('morning', 'Morning'),
                                                 ('noon', 'Noon'),
                                                 ('evening', 'Evening'),
                                                 ('night', 'Night')],
                                      string="Preferred Delivery Slot")
    documents_ids = fields.One2many(comodel_name='partner.document.line',
                                    inverse_name='customer_onboard_id',
                                    string='Documents')
    quotation_doc_filename = fields.Char("Quotation File ")
    quotation_document = fields.Binary(string='Quotation', attachment=True)
    agreement_doc_filename = fields.Char("Agreement File ")
    agreement_document = fields.Binary(string="Agreement", attachment=True)
    pricing_plan_document_ids = fields.One2many(comodel_name='partner.document.line',
                                                inverse_name='pricing_plan_customer_ob_id',
                                                string='Pricing ')
    kyc_upload_document_ids = fields.One2many(comodel_name='partner.document.line',
                                              inverse_name='kyc_customer_ob_id',
                                              string='KYC Document upload')

    quotation_document_ids = fields.One2many(comodel_name='partner.document.line',
                                             inverse_name='quotation_customer_ob_id',
                                             string='Quotation Document upload')

    agreement_document_ids = fields.One2many(comodel_name='partner.document.line',
                                             inverse_name='agreement_customer_ob_id',
                                             string='Agreement Document upload')
    pricing_model = fields.Selection(selection=[('KM', 'KM'),
                                                ('slab', 'SLAB'),
                                                ('flat', 'FLAT')],
                                     string="Pricing Model", default='KM', copy=False)
    km_pricing_plan_ids = fields.One2many(comodel_name='pricing.plan', inverse_name='customer_ob_plan_id',
                                          string='Km Pricing Plan', domain=[('select_plan_type', '=', 'KM')])
    slab_pricing_plan_ids = fields.One2many(comodel_name='pricing.plan', inverse_name='customer_ob_plan_id',
                                            string='Slab Pricing Plan', domain=[('select_plan_type', '=', 'slab')])
    flat_pricing_plan_ids = fields.One2many(comodel_name='pricing.plan', inverse_name='customer_ob_plan_id',
                                            string='Flat Pricing Plan', domain=[('select_plan_type', '=', 'flat')])
    is_approval_user = fields.Boolean(string='Approval User', compute='check_is_approval_user')
    additional_charges_ids = fields.One2many(comodel_name='customer.additional.charges',
                                             inverse_name='customer_onboard_id')
    """ fields for delivery customer"""

    b2b_invoice_tax_ids = fields.Many2many(comodel_name='account.tax', relation='crm_b2b_invoice_tax',
                                           column1='partner_id', column2='tax_id',
                                           string='B2B Invoice Tax')
    b2b_sale_order_tax_ids = fields.Many2many(comodel_name='account.tax', relation='crm_b2b_sale_order_tax',
                                              column1='partner_id', column2='tax_id',
                                              string='B2B Sale Order Tax')
    sms_alert = fields.Selection(selection=[('yes', 'Yes'),
                                            ('no', 'No')],
                                 string="Customer SMS Alert")
    email_alert = fields.Selection(selection=[('yes', 'Yes'),
                                              ('no', 'No')],
                                   string="Customer Email Alert")
    api_selection = fields.Selection([('yes', 'Yes'),
                                      ('no', 'No')],
                                     string="API", default='no', copy=False)
    is_fifo_flow = fields.Selection(selection=[('yes', 'Yes'),
                                               ('no', 'No')], string='FIFO Flow', default='no')
    max_no_de = fields.Integer(string='Max No of DE', default=False)
    is_customer_exist = fields.Boolean(string='Customer Exist', default=False)
    customer_exist_msg = fields.Char(string='Customer exist alert message', store=True)
    is_delivery_service_customer = fields.Boolean(string='Delivery Service', default=False)


    """ fields for qshop customer"""

    qshop_invoice_tax_ids = fields.Many2many(comodel_name='account.tax', relation='crm_invoice_tax',
                                             column1='crm_inv_id', column2='invoice_tax_id',
                                             string='QWQER Shop Invoice Tax')
    qshop_sale_order_tax_ids = fields.Many2many(comodel_name='account.tax', relation='crm_sale_order_tax',
                                                column1='crm_sale_id', column2='sale_tax_id',
                                                string='QWQER Shop Sale Order Tax')
    is_qshop_service_customer = fields.Boolean(string='Qshop Service', default=False)

    """fields for fleet customer"""

    fleet_hsn_id = fields.Many2one(comodel_name='product.product', string='Fleet HSN',
                                   domain="[('fleet_ok','=', True)]")
    vehicle_invoice_tax_ids = fields.Many2many(comodel_name='account.tax', relation='vehicle_invoice_taxes',
                                               column1='partner_id', column2='tax_id',
                                               string='Fleet Tax')
    vehicle_invoice_frequency = fields.Selection(selection=[("weekly", "Weekly"), ("monthly", "Monthly"),
                                                            ], default="weekly", copy=False,
                                                 string="Vehicle Invoice Frequency")
    is_fleet_service_customer = fields.Boolean(string='Fleet Service', default=False)
    is_active_credit_limit  = fields.Boolean(string='Active Credit Limit')
    credit_limit = fields.Float(string='Credit Limit')

    credit_period_id = fields.Many2one(comodel_name='account.payment.term', string='Credit Period')
    contact_designation = fields.Char(string='Contact Designation')
    is_ftl_customer = fields.Boolean(string='Ftl Customer', default=False)
    color = fields.Integer(string="Color", help='Color')

    # @api.depends('payment_mode_ids')
    # def _compute_is_credit_bool(self):
    #     for rec in self:
    #         rec.is_credit_bool = False
    #         for payment in rec.payment_mode_ids:
    #             if payment.is_credit_payment:
    #                 rec.is_credit_bool = True

    @api.onchange('customer_status')
    def onchange_customer_status(self):
        for rec in self:
            if rec.customer_status == 'existing_customer':
                rec.customer_type = 'b2b'

    @api.onchange('phone')
    def _onchange_phone(self):
        """ Check whether the partner exist with same phone number
        """
        if self.phone:
            # Checking Number is valid or not and it contains 10 digits or not
            if re.match(r'^[0-9]+$', self.phone) != None:
                if self.phone and len(self.phone) != 10:
                    raise UserError("Enter valid 10 digits Mobile number")
            else:
                raise ValidationError("Enter valid 10 digits Mobile number")

            # Checking phone number exist or not
            self.is_customer_exist = False
            self.customer_exist_msg = False
            phone = ""
            if self.phone:
                phone = self.phone_code + self.phone
            partner_phone_exist = self.env['res.partner'].search([('phone', '=', phone)])
            if len(partner_phone_exist) > 1:
                raise ValidationError("Multiple Customer/Vendor exist with same phone number")
            if partner_phone_exist:
                customer_type = self.customer_type
                if customer_type == "b2c" and partner_phone_exist.customer_type == "b2c":
                    self.is_customer_exist = True
                    self.customer_exist_msg = "The B2C customer with same number is already exist and the customer details will be updated based on below details."
                elif customer_type == "b2c" and partner_phone_exist.customer_type == "b2b":
                    self.is_customer_exist = True
                    self.phone = ""
                    self.partner_id = False
                    self.customer_exist_msg = "A B2B customer with same phone number is already exist. You are not allowed to create or update B2C customer with same phone number."
                elif customer_type == "b2b" and partner_phone_exist.customer_type == "b2c":
                    self.is_customer_exist = True
                    self.customer_exist_msg = "A B2C customer with same phone number is already exist and customer details will be updated based on below details."
                elif customer_type == "b2b" and partner_phone_exist.customer_type == "b2b":
                    self.is_customer_exist = True
                    self.customer_exist_msg = "A B2B customer with same phone number is already exist and customer details will be updated based on below details."

            customer_ob_phone_exist = self.env['customer.onboard'].search([('phone', '=', self.phone)])
            if customer_ob_phone_exist:
                for customer_ob_phone_exist in customer_ob_phone_exist:
                    raise ValidationError(
                        _('Customer Onboarding Already Exists for this Phone Number  %s . This is Created by  %s  and Created on  %s . So, You Cannot Create New Customer with this Phone Number.') % (
                            self.phone, customer_ob_phone_exist.create_uid.name, customer_ob_phone_exist.create_date))

    def check_is_approval_user(self):
        for rec in self:
            if rec.state == 'draft' and rec.env.user.has_group(
                    'customer_onboarding.customer_onboarding_approval'):
                if rec.user_id == self.env.user:
                    rec.is_approval_user = True
                else:
                    rec.is_approval_user = False
            elif rec.state == 'mu_approvals' and rec.env.user.has_group(
                    'customer_onboarding.customer_onboarding_mu_approval'):
                rec.is_approval_user = True
            elif rec.state == 'finance_approvals' and rec.env.user.has_group(
                    'customer_onboarding.customer_onboarding_finance_approval'):
                rec.is_approval_user = True
            elif rec.state == 'under_pricing_config' and rec.env.user.has_group(
                    'customer_onboarding.customer_onboarding_pricing_approval'):
                rec.is_approval_user = True
            elif rec.state == 'configurations_completed' and rec.env.user.has_group('base.group_system'):
                rec.is_approval_user = True
            elif rec.state == 'rejected':
                rec.is_approval_user = True
            else:
                rec.is_approval_user = False
        if self.env.user.has_group('base.group_system'):
            self.is_approval_user = True


    @api.onchange('customer_service_type_id', 'customer_segment_id')
    def get_service_type(self):
        # Reset all flags initially
        self.is_fleet_service_customer = False
        self.is_delivery_service_customer = False
        self.is_qshop_service_customer = False
        self.is_ftl_customer = False
        self.customer_type = 'b2b'

        if not self.customer_service_type_id:
            return

        # Set flags based on service type
        self.is_fleet_service_customer = self.customer_service_type_id.is_fleet_service
        self.is_delivery_service_customer = self.customer_service_type_id.is_delivery_service
        self.is_qshop_service_customer = self.customer_service_type_id.is_qshop_service

        # Set FTL customer flag if applicable
        if self.is_fleet_service_customer and self.customer_segment_id and self.customer_segment_id.is_ftl:
            self.is_ftl_customer = True

    def action_send_for_approval(self):
        """ send for mu approval """
        # msg = []
        # if self.customer_service_type_id.is_fleet_service:
        #     if not self.customer_email:
        #         msg.append('Customer Email')
        #     if not self.zip:
        #         msg.append('Zip')
        #     if msg:
        #         raise ValidationError("Add values in  " + ", ".join(msg))
        if self.customer_service_type_id.is_delivery_service or self.customer_service_type_id.is_qshop_service:
            if self.is_fifo_flow == 'yes' and self.max_no_de <= 0.0:
                raise UserError(_("Maximum Number of De should be Greater than zero"))
        #     if not self.zip:
        #         msg.append('Zip')
        #     if self.customer_type == 'b2b':
        #         if not self.potential_orders_id:
        #             msg.append('Potential Orders')
        #         if not self.delivery_type_id:
        #             msg.append('Type of Delivery')
        #         if not self.distance_limitation:
        #             msg.append('Distance Limitation')
        #         if not self.industry_id:
        #             msg.append('Customer Industry')
        #
        #     if msg:
        #         raise ValidationError("Add values in " + ", ".join(msg))

        form_view_id = self.env.ref('customer_onboarding.customer_onboard_send_for_approval_form_view').id
        self.comments = ""
        return {
            'name': "Send for Approval",
            'view_type': 'form',
            'target': 'new',
            "view_mode": 'form',
            'res_model': 'customer.onboard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_id': form_view_id,
        }

    def action_approved(self):
        msg = []
        if self.customer_service_type_id.is_fleet_service:
            if not self.customer_email:
                msg.append('Customer Email')
            if not self.zip:
                msg.append('Zip')
        if self.customer_service_type_id.is_delivery_service or self.customer_service_type_id.is_qshop_service:
            if not self.customer_email:
                msg.append('Customer Email')
            if not self.zip:
                msg.append('Zip')
            if self.customer_type == 'b2b':
                if not self.delivery_type_id:
                    msg.append('Type of Delivery')
                if not self.distance_limitation:
                    msg.append('Distance Limitation')
                if not self.pick_up_area:
                    msg.append('Pick-up Area')
                if not self.payment_mode_ids:
                    msg.append('Payment Mode')
        if msg:
            raise ValidationError("Add values in " + ", ".join(msg))
        if not self.is_fleet_service_customer:
            if self.pricing_model:
                if  len(self.km_pricing_plan_ids) == 0 and  len(self.slab_pricing_plan_ids) == 0 and len(self.flat_pricing_plan_ids) == 0:
                    raise UserError(_("Pricing Plan not found. Please add at least one item in pricing plan"))
        state_from = 'draft'
        state_to = 'mu_approvals'
        self.create_user_history(state_from, state_to)
        email_template = self.env.ref(
            'customer_onboarding.customer_onboard_mu_approve_send_mail')
        email_template.send_mail(self.id, email_values=None, force_send=True)
        self.state = 'mu_approvals'

    def action_mu_approval(self):
        form_view_id = self.env.ref('customer_onboarding.customer_onboard_send_for_approval_form_view').id
        self.comments = ""
        self.mu_pricing_plan_status = False
        self.mu_agreement_status = False
        self.mu_payment_option_status = False
        return {
            'name': "Send for Approval",
            'view_type': 'form',
            'target': 'new',
            "view_mode": 'form',
            'res_model': 'customer.onboard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_id': form_view_id,
        }

    def action_mu_approved(self):
        if self.customer_service_type_id.is_delivery_service or self.customer_service_type_id.is_qshop_service:
            if not self.agreement_document:
                raise UserError('Agreement not found. Please upload the agreement.')
        state_from = 'mu_approvals'
        state_to = 'finance_approvals'
        self.create_user_history(state_from, state_to)
        self.approval_send_email()
        self.state = 'finance_approvals'

    def action_mu_rejected(self):
        state_from = 'mu_approvals'
        state_to = 'draft'
        self.create_user_history(state_from, state_to)
        email_template = self.env.ref(
            'customer_onboarding.customer_onboard_mu_rejected_send_mail')
        if email_template:
            if self.id:
                email_template.send_mail(self.id, email_values=None, force_send=True)
        self.state = 'draft'

    def action_finance_approval(self):
        form_view_id = self.env.ref('customer_onboarding.customer_onboard_send_for_approval_form_view').id
        self.comments = ""
        return {
            'name': "Send for Approval",
            'view_type': 'form',
            'target': 'new',
            "view_mode": 'form',
            'res_model': 'customer.onboard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_id': form_view_id,
        }

    def action_finance_approved(self):
        msg = []
        if self.customer_service_type_id.is_fleet_service:
            if not self.vehicle_invoice_tax_ids:
                msg.append('Fleet Tax')
        if self.customer_service_type_id.is_delivery_service:
            if not self.b2b_invoice_tax_ids:
                msg.append('B2B Tax Invoice')
            if not self.b2b_sale_order_tax_ids:
                msg.append('B2B Sale Order Tax')
        if self.customer_service_type_id.is_qshop_service:
            if not self.qshop_invoice_tax_ids:
                msg.append('Qshop B2B Tax Invoice')
            if not self.qshop_sale_order_tax_ids:
                msg.append('Qshop B2B Sale Order Tax')
        if not self.street:
            msg.append('Street')
        if not self.city:
            msg.append('City')
        if not self.state_id:
            msg.append('State')
        if not self.zip:
            msg.append('Zip')
        if msg:
            raise ValidationError("Please Fill " + ", ".join(msg))
        if self.gstin_number:
            if len(self.gstin_number) != 15:
                raise ValidationError(
                    _('The GSTIN [%s]  should be 15 characters only.') % self.gstin_number)
        if self.customer_service_type_id.is_fleet_service:
            return self.action_approve_pricing()
        else:
            state_from = 'finance_approvals'
            state_to = 'under_pricing_config'
            self.create_user_history(state_from, state_to)
            self.state = 'under_pricing_config'

    def action_finance_rejected(self):
        state_from = 'finance_approvals'
        state_to = 'mu_approvals'
        self.create_user_history(state_from, state_to)
        email_template = self.env.ref(
            'customer_onboarding.customer_onboard_finance_rejected_send_mail')
        if email_template:
            if self.id:
                email_template.send_mail(self.id, email_values=None, force_send=True)
        self.state = 'mu_approvals'

    def action_pricing_approval(self):
        form_view_id = self.env.ref('customer_onboarding.customer_onboard_send_for_approval_form_view').id
        self.comments = ""
        return {
            'name': "Pricing Configuration",
            'view_type': 'form',
            'target': 'new',
            "view_mode": 'form',
            'res_model': 'customer.onboard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_id': form_view_id,
        }

    def action_approve_pricing(self):
        if not self.partner_id:
            phone = ""
            if self.phone:
                phone = self.phone_code + self.phone
            existing_customer = self.env['res.partner'].search([('phone', '=', phone)])
            if existing_customer:
                if self.customer_type == 'b2c' and existing_customer.customer_type == 'b2c':
                    message_id = self.env['message.wizard'].create({'message': _(
                        "The B2C customer with same number is already exist and Do you Want to updated the customer with the given details?")})
                    return {
                        'name': _('Warning'),
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'message.wizard',
                        'res_id': message_id.id,
                        'target': 'new'
                    }
                elif self.customer_type == "b2c" and existing_customer.customer_type == "b2b":

                    message_id = self.env['message.wizard'].create({'is_warning': 1, 'message': _(
                        "A B2B customer with same phone number is already exist. You are not allowed to create or update B2B customer with same phone number with B2C customer type")})
                    return {
                        'name': _('Warning'),
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'message.wizard',
                        'res_id': message_id.id,
                        'target': 'new'
                    }
                elif self.customer_type == "b2b" and existing_customer.customer_type == "b2c":

                    message_id = self.env['message.wizard'].create({'message': _(
                        "A B2C customer with same phone number is already exist. Do you want to updated the customer with the given details? ")})
                    return {
                        'name': _('Warning'),
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'message.wizard',
                        # pass the id
                        'res_id': message_id.id,
                        'target': 'new'
                    }
                elif self.customer_type == "b2b" and existing_customer.customer_type == "b2b":

                    message_id = self.env['message.wizard'].create({'message': _(
                        "A B2B customer with same phone number is already exist and updated the customer with the given details? ")})
                    return {
                        'name': _('Successfull'),
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'message.wizard',
                        # pass the id
                        'res_id': message_id.id,
                        'target': 'new'
                    }
            else:
                partner = self.create_customer()
                if partner:
                    self.state = 'configurations_completed'
                    state_from = 'under_pricing_config'
                    state_to = 'configurations_completed'
                    self.create_user_history(state_from, state_to)
        return True

    def action_reject_pricing(self):
        state_from = 'under_pricing_config'
        state_to = 'finance_approvals'
        self.state = 'finance_approvals'
        self.create_user_history(state_from, state_to)

    def create_customer(self):
        """ create customer when new customer onboarded"""
        state = self.state_id.id
        # Initialize the phone number
        phone = self.phone_code + self.phone if self.phone else ""
        if self.phone:
            phone = self.phone_code + self.phone
        if not self.state_id:
            state = self.region_id.state_id.id
        is_a_sub_customer = False
        if self.parent_partner_id:
            is_a_sub_customer = True
        dict_vals = {
            'name': self.customer_name,
            'brand_name': self.brand_name or False,
            'is_company': True,
            'customer_rank': 1,
            'email': self.customer_email,
            'street': self.street,
            'street2': self.street2,
            'city': self.city,
            'state_id': state,
            'zip': self.zip,
            'country_id': self.country_id.id,
            'active': True,
            'vat': self.gstin_number,
            'l10n_in_pan': self.tax_id,
            'customer_type': self.customer_type,
            'phone': phone,
            'mobile': phone,
            'region_id': self.region_id.id,
            'state_region_id' : self.region_id.state_id.id,
            'order_sales_person': self.sales_person_id.id,
            'source_lead_type_id': self.source_id.id,
            'industry_id': self.industry_id.id,
            'followup_status_id': self.followup_status_id.id,
            'pricing_type': self.pricing_type,
            'payment_mode_ids': self.payment_mode_ids.ids,
            'potential_orders_id': self.potential_orders_id.id or False,
            'delivery_type_id': self.delivery_type_id.id or False,
            'pick_up_area': self.pick_up_area or False,
            'distance_limitation': self.distance_limitation or False,
            'api_selection': self.api_selection or False,
            'product_storage': self.product_storage or False,
            'product_sorting': self.product_sorting or False,
            'item_category_id': self.item_category_id.id or False,
            'sms_alert': self.sms_alert or False,
            'email_alert': self.email_alert or False,
            'service_type_id': self.customer_service_type_id.id or False,
            'segment_id': self.customer_segment_id.id or False,
            'product_line_id': self.product_line_id.id or False,
            'credit_period_id': self.credit_period_id.id or False,
            'pricing_model': self.pricing_model or False,
            'contact_designation': self.contact_designation or False,
            # 'is_credit_bool': self.is_credit_bool or False,
            'merchant_amount_collection': self.merchant_amount_collection or False,
            'amount_collection_limit': self.amount_collection_limit or False,
            'amount_collection_sign': self.amount_collection_sign or False,
            'settlement_time_id': self.settlement_time_id.id or False,
            'collection_charges': self.collection_charges or False,
            'collection_charges_sign': self.collection_charges_sign or False,
            'is_a_sub_customer': is_a_sub_customer,
            'parent_partner_id': self.parent_partner_id.id,
            'submerchant_billing': self.submerchant_billing,
            'invoice_frequency_id':self.invoice_frequency_id.id or False,
            'active_limit':self.is_active_credit_limit or False,
            'blocking_stage': self.credit_limit or False,
            'is_fifo_flow': self.is_fifo_flow or False,
            'max_no_de': self.max_no_de or False,

        }
        if self.is_fleet_service_customer:
            if self.is_fleet_service_customer:
                dict_vals.update({
                    'vehicle_invoice_tax_ids': [
                        (6, 0, self.vehicle_invoice_tax_ids.ids)] if self.vehicle_invoice_tax_ids else False,
                    'fleet_hsn_id': self.fleet_hsn_id.id or False,
                    'frequency': self.vehicle_invoice_frequency or False,
                    'is_fleet_partner': True
                })
        if self.is_delivery_service_customer:
            dict_vals.update({
                'b2b_invoice_tax_ids': [
                    (6, 0, self.b2b_invoice_tax_ids.ids)] if self.b2b_invoice_tax_ids.ids else False,
                'b2b_sale_order_tax_ids': [
                    (6, 0, self.b2b_sale_order_tax_ids.ids)] if self.b2b_sale_order_tax_ids.ids else False,
                'is_delivery_customer': True
            })
        if self.is_qshop_service_customer:
            dict_vals.update({
                'qshop_sale_order_tax_ids': [
                    (6, 0, self.qshop_sale_order_tax_ids.ids)] if self.qshop_sale_order_tax_ids.ids else False,
                'qshop_invoice_tax_ids': [
                    (6, 0, self.qshop_invoice_tax_ids.ids)] if self.qshop_invoice_tax_ids.ids else False,
                'is_qshop_customer': True
            })
        partner = self.env['res.partner'].create(dict_vals)
        if partner:
            self.partner_id = partner.id
            if self.km_pricing_plan_ids:
                for rec in self.km_pricing_plan_ids:
                    rec.partner_id = partner.id
            if self.slab_pricing_plan_ids:
                for rec in self.slab_pricing_plan_ids:
                    rec.partner_id = partner.id
            if self.flat_pricing_plan_ids:
                for rec in self.flat_pricing_plan_ids:
                    rec.partner_id = partner.id
            if self.additional_charges_ids:
                for rec in self.additional_charges_ids:
                    rec.partner_id = partner.id
            if self.documents_ids:
                for rec in self.documents_ids:
                    rec.partner_id = partner.id
            if self.kyc_upload_document_ids:
                for rec in self.kyc_upload_document_ids:
                    rec.partner_id = partner.id
            partner.action_activate_wallet()
            # create contact for created partner
            contact_partner = self.env['res.partner'].create({'name': self.contact_name,
                                                              'type': 'contact',
                                                              'email': self.customer_email,
                                                              'street': self.street,
                                                              'street2': self.street2,
                                                              'city': self.city,
                                                              'state_id': state,
                                                              'zip': self.zip,
                                                              'country_id': self.country_id.id,
                                                              'parent_id': partner.id,
                                                              'active': True,
                                                              'customer_type': self.customer_type,
                                                              'sms_alert': self.sms_alert or False,
                                                              'email_alert': self.email_alert or False,
                                                              'segment_id': self.customer_segment_id.id or False,
                                                              })
            self.contact_partner_id = contact_partner.id
            return partner,dict_vals

    def action_reject(self):
        form_view_id = self.env.ref('customer_onboarding.customer_onboard_lost_form_view').id
        self.comments = ""
        return {
            'name': "Rejected",
            'view_type': 'form',
            'target': 'new',
            "view_mode": 'form',
            'res_model': 'customer.onboard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_id': form_view_id,
        }

    def action_reject_confirm(self):
        state_from = self.state
        state_to = 'rejected'
        self.create_user_history(state_from, state_to)
        self.state = 'rejected'

    def reset_to_draft(self):
        form_view_id = self.env.ref('customer_onboarding.customer_onboard_reset_to_draft_form_view').id
        self.comments = ""
        return {
            'name': "Reset To Draft",
            'view_type': 'form',
            'target': 'new',
            "view_mode": 'form',
            'res_model': 'customer.onboard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_id': form_view_id,
        }

    def confirm_reset_to_draft(self):
        state_from = self.state
        state_to = 'draft'
        self.create_user_history(state_from, state_to)
        self.state = 'draft'

    def create_user_history(self, state_from, state_to):
        """ updating user action history table"""

        values = {
            'user_id': self.env.user.id,
            'description': self.comments,
            'action_customer_onboard_id': self.id,
            'last_updated_on': datetime.today(),
            'state_from': state_from,
            'state_to': state_to,
        }
        self.env['onboard.user.action.history'].create(values)
        return True

    @api.onchange('sales_person_id')
    def get_corresponding_user(self):
        """ get corresponding user and mu of the sales person"""
        for rec in self:
            if rec.sales_person_id and rec.state:
                rec.user_id = rec.sales_person_id.user_id.id or False
                rec.reporting_mu_id = rec.sales_person_id.mu_id.id or False

    @api.onchange('parent_partner_id')
    def _onchange_parent_partner_id(self):
        for rec in self:
            if rec.parent_partner_id and rec.parent_partner_id.phone:
                rec.merchant_phone_number = rec.parent_partner_id.phone

    def action_change_sale_executive(self):
        form_view_id = self.env.ref('customer_onboarding.assign_sale_person_view_form').id
        self.comments = ""
        return {
            'name': "Assign Sale Executive",
            'view_type': 'form',
            'target': 'new',
            "view_mode": 'form',
            'res_model': 'customer.onboard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_id': form_view_id,
        }

    def action_assign_sale_executive(self):
        if self.sales_person_id:
            self.get_corresponding_user()

    @api.model
    def create(self, vals_list):
        rec = super(CustomerOnboard, self).create(vals_list)
        # creating user comments
        if rec.user_comment:
            self.env['user.comments'].create({
                'user_id': rec.env.user.id,
                'user_comment': rec.user_comment,
                'comment_customer_onboard_id': rec.id,
                'commented_on': datetime.today()
            })
            self.user_comment = ""
        if rec:
            rec.approval_send_email()
        return rec

    def write(self, vals):
        """override the write function removing the other pricing plan when new one added"""
        vals.update({'last_updated_on': datetime.today()})
        result = super(CustomerOnboard, self).write(vals)
        if 'sales_person_id' in vals:
            self.approval_send_email()
        if 'pricing_model' in vals:
            # Determine which pricing plan ids are being updated
            plan_fields = {
                'slab_pricing_plan_ids': ['km_pricing_plan_ids', 'flat_pricing_plan_ids'],
                'flat_pricing_plan_ids': ['km_pricing_plan_ids', 'slab_pricing_plan_ids'],
                'km_pricing_plan_ids': ['flat_pricing_plan_ids', 'slab_pricing_plan_ids']
            }

            for plan, others in plan_fields.items():
                if vals.get(plan):
                    for field in others:
                        getattr(self, field).unlink()

        for rec in self:
            if rec.street and len(rec.street) > 100 or rec.street2 and len(rec.street2) > 100:
                raise UserError(_("Address line should not exceed 100 words"))
            if rec.customer_service_type_id.is_fleet_service:
                if rec.is_active_credit_limit and rec.credit_limit <= 0:
                    raise UserError(_("Credit Limit should be Greater than zero"))
            if rec.customer_service_type_id.is_delivery_service or rec.customer_service_type_id.is_qshop_service:
                if rec.merchant_amount_collection == 'yes' and rec.amount_collection_limit == 0.0:
                    raise UserError(_("Merchant Amount Collection should be Greater than zero"))
                if rec.is_fifo_flow == 'yes' and rec.max_no_de <= 0:
                    raise UserError(_("Maximum Number of De should be Greater than zero"))
                if rec.state != "draft" and self.customer_type == 'b2b':
                    msg = []
                    if not self.pick_up_area:
                        msg.append("Pick-up Area")
                    if not self.delivery_type_id:
                        msg.append("Type of Delivery")
                    if not self.payment_mode_ids:
                        msg.append("Payment Modes")
                    if not self.distance_limitation:
                         msg.append("Distance Limitation")
                    if self.pricing_model=='KM' and len(self.km_pricing_plan_ids) == 0:
                        msg.append('KM Pricing Plan')
                    if self.pricing_model=='flat' and len(self.flat_pricing_plan_ids) == 0:
                        msg.append('Flat Pricing Plan')
                    if self.pricing_model=='slab' and len(self.slab_pricing_plan_ids) == 0:
                        msg.append('Slab Pricing Plan')
                    if msg:
                        raise ValidationError("Please Fill " + ", ".join(msg))

        # creating user comments
        if self.user_comment:
            self.env['user.comments'].create({
                'user_id': self.env.user.id,
                'user_comment': self.user_comment,
                'comment_customer_onboard_id': self.id,
                'commented_on': datetime.today()
            })
            self.user_comment = ""
        return result

    def approval_send_email(self):
        email_template = False
        if self.state == 'draft':
            email_template = self.env.ref(
                'customer_onboarding.new_customer_onboard_send_mail')
        if self.state == 'mu_approvals':
            email_template = self.env.ref(
                'customer_onboarding.customer_onboard_finance_approve_send_mail')
        if email_template:
            if self.id:
                email_template.send_mail(self.id, email_values=None, force_send=True)

    @api.onchange('customer_service_type_id')
    def onchange_customer_service_type(self):
        new_list = []
        self.customer_segment_id = False
        if self.customer_service_type_id.is_fleet_service:
            fleet_customer_segment_ids = self.env['partner.segment'].search(
                [('is_fleet_service', '=', True), ('is_customer', '=', True),('company_id','=',self.company_id.id)])
            if fleet_customer_segment_ids:
                for segment_id in fleet_customer_segment_ids:
                    new_list.append(segment_id.id)
                return {'domain': {'customer_segment_id': [('id', 'in', new_list)]}}
        else:
            customer_segment_ids = self.env['partner.segment'].search(
                [('is_fleet_service', '=', False), ('is_customer', '=', True),('company_id','=',self.company_id.id)])
            if customer_segment_ids:
                for segment_id in customer_segment_ids:
                    new_list.append(segment_id.id)
                return {'domain': {'customer_segment_id': [('id', 'in', new_list)]}}

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # if self.env.user.id != SUPERUSER_ID:
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    args.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    args.append(('region_id', 'in', []))
        res = super(CustomerOnboard, self).search(args, offset, limit, order, count=count)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    domain.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    domain.append(('region_id', 'in', []))
        return super(CustomerOnboard, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)

    def _group_expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    def action_view_customer(self):
        """to view the customer  through smart button in onboard view"""
        form_view = self.env.ref('base.view_partner_form')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'view_id': form_view.id,
            'context': {'create': False, 'default_customer_rank': 1},
            'target': 'current',
        }


    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id

    def check_access_rule(self, operation):
        # Call the super method to check access
        try:
            super(CustomerOnboard, self).check_access_rule(operation)
        except AccessError as e:
            # Raise custom error message if access is denied
            _logger.info("Error :exception happened : %s", e)
            raise AccessError(
                _("You do not have the required permissions to access this record. Please contact the system administrator."))
