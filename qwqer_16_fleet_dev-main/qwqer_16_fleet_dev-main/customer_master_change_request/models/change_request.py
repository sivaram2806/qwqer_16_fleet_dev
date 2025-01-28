from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo import SUPERUSER_ID
from collections import Counter


class CustomerMasterChangeReq(models.Model):
    _name = 'customer.master.change.request'
    _rec_name = 'rec_no'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def get_states(self):
        user = self.env.user
        user_country_id = user.company_id.country_id
        return [('country_id', '=', user_country_id.id)]

    def get_customer(self):
        if self.env.user.has_group('qw_service_extension.kpi_report_region_filter_group'):
            return [('region_id', 'in', self.env.user.displayed_regions_ids.ids)]

    rec_no = fields.Char(string='Record No', copy=False, readonly=True, default=lambda self: _('New'))
    customer_id = fields.Many2one(comodel_name='res.partner', string='Customer Name', tracking=True,
                                  domain=get_customer)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    type = fields.Selection(related='customer_id.customer_type', string='Customer Type', tracking=True)
    phn_number = fields.Char(related='customer_id.phone', string='Phone Number')
    region_id = fields.Many2one(related='customer_id.region_id')
    customer_service_type_id = fields.Many2one(related='customer_id.service_type_id', tracking=True)
    field_to_change = fields.Many2many(comodel_name='change.field', relation='field_to_change_rel', tracking=True)
    change_field_domain = fields.Many2many(comodel_name='change.field', relation='change_field_domain_rel',
                                           compute='_compute_change_field_domain', store=True)

    state = fields.Selection(selection=[('new', 'New'), ('mu_approval_pending', 'Under UH Approval'),
                                        ('fin_approval_pending', 'Under Finance Approval'), ('approved', 'Approved'),
                                        ('rejected', 'Rejected')], default='new', tracking=True)
    user_action_ids = fields.One2many(comodel_name='user.action.log', inverse_name='change_req_id', string='Log')

    # changing fields
    street = fields.Char(tracking=True)
    street2 = fields.Char(tracking=True)
    zip = fields.Char(change_default=True, tracking=True)
    city = fields.Char(tracking=True)
    state_id = fields.Many2one(comodel_name="res.country.state", string='State', ondelete='restrict',
                               domain=get_states, tracking=True)
    country_id = fields.Many2one(comodel_name='res.country', string='Country', ondelete='restrict', tracking=True)
    payment_mode_ids = fields.Many2many(comodel_name='payment.mode', string='Payment Mode', tracking=True)
    invoice_frequency_id = fields.Many2one(comodel_name='invoice.frequency', string='Invoice Frequency', tracking=True)
    vat = fields.Char(string='GSTIN',
                      help="The Tax Identification Number. Complete it if the contact "
                           "is subjected to government taxes. Used in some legal statements.", tracking=True)
    l10n_in_pan = fields.Char(string='PAN', tracking=True)
    sms_alert = fields.Selection(selection=[('yes', 'Yes'),
                                            ('no', 'No')],
                                 string="Customer SMS Alert", tracking=True)
    email_alert = fields.Selection(selection=[('yes', 'Yes'),
                                              ('no', 'No')],
                                   string="Customer Email Alert", tracking=True)
    segment_id = fields.Many2one(comodel_name="partner.segment", string='Customer Segment', tracking=True,
                                          domain="[('is_fleet_service', '=', False)]")
    fleet_customer_segment_id = fields.Many2one(comodel_name="partner.segment", string='Customer Segment',
                                                tracking=True,
                                                domain="[('is_fleet_service', '=', True)]")
    source_lead_type_id = fields.Many2one(comodel_name='utm.source', string="Source/Lead Type", tracking=True)
    industry_id = fields.Many2one(comodel_name='res.partner.industry', string='Customer Industry', store=True,
                                  tracking=True)
    potential_orders_id = fields.Many2one(comodel_name='potential.orders', string="Potential Orders", copy=False,
                                          tracking=True)
    delivery_type_id = fields.Many2one(comodel_name='delivery.type', string='Type of Delivery', copy=False,
                                       tracking=True)
    pick_up_area = fields.Text(string="Pick up Area", tracking=True)
    item_category_id = fields.Many2one(comodel_name="item.category", string="Item Category")
    followup_status_id = fields.Many2one(comodel_name="mail.activity.type", string="Follow-up Status")
    fleet_hsn_id = fields.Many2one(comodel_name='product.product', string='Fleet HSN',domain="[('fleet_ok','=', True)]")
    credit_period_id = fields.Many2one(comodel_name='account.payment.term', string='Credit Period')
    contract_id = fields.Many2one(comodel_name='vehicle.contract', string='Contract Number')
    contact_designation = fields.Char(string='Contact Designation')

    pricing_type = fields.Selection(selection=[('default', 'Default Pricing'),
                                               ('special', 'Special Pricing')],
                                    string="Pricing Type", tracking=True)

    tds_threshold_check = fields.Boolean(tracking=True)
    customer_type = fields.Selection(selection=[('b2c', 'B2C'), ('b2b', 'B2B')], string='Customer Type', store=True,
                                     tracking=True)
    order_sales_person = fields.Many2one(comodel_name='hr.employee', string='Order Sales Person', tracking=True)
    api_selection = fields.Selection(selection=[('yes', 'Yes'),
                                                ('no', 'No')],
                                     string="API", default='no', copy=False, tracking=True)

    distance_limitation = fields.Float(string="Distance Limitation", copy=False, tracking=True)
    merchant_amount_collection = fields.Selection(selection=[('yes', 'Yes'),
                                                             ('no', 'No')],
                                                  string="Merchant Amount Collection", tracking=True, copy=False)
    amount_collection_limit = fields.Float(string="Amount Collection Limit", tracking=True, copy=False)
    amount_collection_sign = fields.Char(string="Amount Collection Sign", default="Rs", tracking=True, copy=False)
    settlement_time_id = fields.Many2one(comodel_name='settlement.time', string='Settlement Time', tracking=True,
                                         copy=False)
    collection_charges = fields.Float(string="Collection Charges", tracking=True, copy=False)
    collection_charges_sign = fields.Char(string="Collection Charges Sign", default="%", tracking=True, copy=False)
    comment = fields.Text(string='Comments', copy=False)
    pricing_model = fields.Selection(selection=[('KM', 'KM'),
                                                ('slab', 'SLAB'),
                                                ('flat', 'FLAT')],
                                     string="Pricing Model", default='KM', copy=False, tracking=True)
    agreement_document = fields.Binary(string="Agreement", attachment=False, copy=False)
    is_fifo_flow = fields.Selection(selection=[
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='FIFO Flow', default='no')
    max_no_de = fields.Integer(string='Max No of DE', default=False)
    product_line_id = fields.Many2one(comodel_name="product.lines", string="Product Lines", tracking=True)
    source_type_id = fields.Many2one(comodel_name="source.type", string="Order Placement")
    active_limit  = fields.Boolean(string='Active Credit Limit')
    blocking_stage = fields.Float(string='Credit Limit')
    # pricing plan details for changing
    new_km_pricing_plan_ids = fields.One2many(comodel_name='pricing.plan', inverse_name='change_req_id',
                                              string='Km Pricing Plan', domain=[('select_plan_type', '=', 'KM')])
    new_slab_pricing_plan_ids = fields.One2many(comodel_name='pricing.plan', inverse_name='change_req_id',
                                                string='Slab Pricing Plan', domain=[('select_plan_type', '=', 'slab')])
    new_flat_pricing_plan_ids = fields.One2many(comodel_name='pricing.plan', inverse_name='change_req_id',
                                                string='Flat Pricing Plan', domain=[('select_plan_type', '=', 'flat')])
    # pricing plan One2many for keeping the history of res partner pricing plan
    previous_pricing_model = fields.Selection(selection=[('KM', 'KM'),
                                                         ('slab', 'SLAB'),
                                                         ('flat', 'FLAT')],
                                              string="Pricing Model", default='KM', copy=False, tracking=True)
    previous_km_pricing_plan_ids = fields.One2many(comodel_name='pricing.plan', inverse_name='previous_change_req_id',
                                                   string='Km Pricing Plan', domain=[('select_plan_type', '=', 'KM')])
    previous_slab_pricing_plan_ids = fields.One2many(comodel_name='pricing.plan', inverse_name='previous_change_req_id',
                                                     string='Slab Pricing Plan',
                                                     domain=[('select_plan_type', '=', 'slab')])
    previous_flat_pricing_plan_ids = fields.One2many(comodel_name='pricing.plan', inverse_name='previous_change_req_id',
                                                     string='Flat Pricing Plan',
                                                     domain=[('select_plan_type', '=', 'flat')])
    # additional charge details
    new_additional_charges_ids = fields.One2many(comodel_name='customer.additional.charges',
                                                 inverse_name='change_request_id')

    previous_additional_charges_ids = fields.One2many(comodel_name='customer.additional.charges',
                                                      inverse_name='previous_change_request_id')

    # boolean check
    is_address = fields.Boolean(copy=False)
    is_payment_mode = fields.Boolean(copy=False)
    is_invoice_frequency_id = fields.Boolean(copy=False)
    is_vat = fields.Boolean(copy=False)
    is_tax_id = fields.Boolean(copy=False)
    is_sms_alert = fields.Boolean(copy=False)
    is_email_alert = fields.Boolean(copy=False)
    is_customer_segment_id = fields.Boolean(copy=False, store=True)
    is_fleet_customer_segment_id = fields.Boolean(copy=False, store=True)
    is_source_lead_type_id = fields.Boolean(copy=False)
    is_potential_orders_id = fields.Boolean(copy=False)
    is_industry_id = fields.Boolean(copy=False)
    is_delivery_type_ids = fields.Boolean(copy=False)
    is_pick_up_area = fields.Boolean(copy=False)
    is_pricing_type = fields.Boolean(copy=False)
    is_tds = fields.Boolean(copy=False)
    is_item_category_id = fields.Boolean(copy=False)
    is_customer_type = fields.Boolean(copy=False)
    is_order_sales_person = fields.Boolean(copy=False)
    is_api_selection = fields.Boolean(copy=False)
    is_distance_limitation = fields.Boolean(copy=False)
    is_followup_status_id = fields.Boolean(copy=False)
    is_fleet_hsn_id = fields.Boolean(copy=False)
    is_credit_period_id = fields.Boolean(copy=False)
    is_contract_id = fields.Boolean(copy=False)
    is_contact_designation = fields.Boolean(copy=False)
    is_fleet_customer_segment = fields.Boolean(copy=False)
    is_fifo = fields.Boolean(copy=False)
    is_price_plan = fields.Boolean(copy=False, default=False)
    is_proceed = fields.Boolean(copy=False, default=False)
    is_user = fields.Boolean(default=False)
    is_mu_user = fields.Boolean(default=False)
    is_fn_user = fields.Boolean(default=False)
    is_stop_charge = fields.Boolean(string="Is Additional Charge", copy=False)
    is_product_line = fields.Boolean(string="Is Product Line", copy=False)
    is_source = fields.Boolean(string="Is Order Placement", copy=False)
    is_approval_user = fields.Boolean(string='Approval User', compute='check_is_approval_user')
    is_submitted = fields.Boolean(copy=False, default=False)
    is_credit_limit = fields.Boolean(copy=False, default=False)
    is_merchant_collection = fields.Boolean(copy=False,default=False)

    @api.depends('customer_id')
    def _compute_change_field_domain(self):
        for rec in self:
            if rec.customer_id and rec.customer_service_type_id:
                if rec.customer_id.is_delivery_customer or rec.customer_id.is_qshop_customer:
                    delivery_qshop_change_field_ids = self.env['change.field'].search(
                        [('is_delivery_service_field', '=', True)])
                    if delivery_qshop_change_field_ids:
                        rec.change_field_domain = delivery_qshop_change_field_ids
                if rec.customer_id.is_fleet_partner:
                    if rec.customer_id.is_ftl_customer:
                        fleet_ftl_change_field_ids = self.env['change.field'].search(
                            [('is_ftl_service_field', '=', True)])
                        if fleet_ftl_change_field_ids:
                            rec.change_field_domain = fleet_ftl_change_field_ids
                    else:
                        fleet_change_field_ids = self.env['change.field'].search(
                            [('is_fleet_service_field', '=', True)])
                        if fleet_change_field_ids:
                            rec.change_field_domain = fleet_change_field_ids
            else:
                rec.change_field_domain = []
    @api.depends('state')
    def check_is_approval_user(self):
        for rec in self:
            if rec.state == 'new':
                if rec.create_uid.id == self.env.user.id:
                    rec.is_approval_user = True
                else:
                    if self.id:
                        rec.is_approval_user = False
                    else:
                        rec.is_approval_user = True

            elif rec.state == 'mu_approval_pending' and rec.env.user.has_group(
                    'customer_onboarding.customer_onboarding_mu_approval'):
                rec.is_approval_user = True
            elif rec.state == 'fin_approval_pending' and rec.env.user.has_group(
                    'customer_onboarding.customer_onboarding_finance_approval'):
                rec.is_approval_user = True
            elif rec.state == 'approved' and rec.env.user.has_group('base.group_system'):
                rec.is_approval_user = True
            else:
                rec.is_approval_user = False

    # filtering of change field by customer service type
    # @api.onchange('customer_id')
    # def onchange_customer_service_type(self):
    #     self.field_to_change = False
    #     if self.customer_id:
    #         new_list = []
    #         if self.customer_id.is_delivery_customer or self.customer_id.is_qshop_customer:
    #             delivery_qshop_change_field_ids = self.env['change.field'].search(
    #                 [('is_delivery_service_field', '=', True)])
    #             if delivery_qshop_change_field_ids:
    #                 for change_field in delivery_qshop_change_field_ids:
    #                     new_list.append(change_field.id)
    #                 return {'domain': {'field_to_change': [('id', 'in', new_list)]}}
    #         if self.customer_id.is_fleet_partner:
    #             if self.customer_id.is_ftl_customer:
    #                 fleet_ftl_change_field_ids = self.env['change.field'].search(
    #                     [('is_ftl_service_field', '=', True)])
    #                 if fleet_ftl_change_field_ids:
    #                     for change_field in fleet_ftl_change_field_ids:
    #                         new_list.append(change_field.id)
    #                     return {'domain': {'field_to_change': [('id', 'in', new_list)]}}
    #             else:
    #                 fleet_change_field_ids = self.env['change.field'].search(
    #                     [('is_fleet_service_field', '=', True)])
    #                 if fleet_change_field_ids:
    #                     for change_field in fleet_change_field_ids:
    #                         new_list.append(change_field.id)
    #                     return {'domain': {'field_to_change': [('id', 'in', new_list)]}}
    #     else:
    #         pass

    # when pricing plan changed the attachment will remove
    @api.onchange('select_plan_km_ids', 'select_plan_slab_ids', 'select_plan_flat_ids')
    def pricing_plan_changed(self):
        if self.new_km_pricing_plan_ids:
            self.agreement_document = False
        if self.new_slab_pricing_plan_ids:
            self.agreement_document = False
        if self.new_flat_pricing_plan_ids:
            self.agreement_document = False

    def write(self, values):
        result = super(CustomerMasterChangeReq, self).write(values)

        if 'pricing_model' in values:
            # Determine which pricing plan ids are being updated
            plan_fields = {
                'new_slab_pricing_plan_ids': ['new_km_pricing_plan_ids', 'new_flat_pricing_plan_ids'],
                'new_flat_pricing_plan_ids': ['new_km_pricing_plan_ids', 'new_slab_pricing_plan_ids'],
                'new_km_pricing_plan_ids': ['new_flat_pricing_plan_ids', 'new_slab_pricing_plan_ids']
            }
            for plan, others in plan_fields.items():
                if values.get(plan):
                    for field in others:
                        getattr(self, field).unlink()
        return result


    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # if self.env.user.id != SUPERUSER_ID:
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qw_service_extension.kpi_report_region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    args.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    args.append(('region_id', 'in', []))
        res = super(CustomerMasterChangeReq, self).search(args, offset, limit, order, count=count)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qw_service_extension.kpi_report_region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    domain.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    domain.append(('region_id', 'in', []))
        return super(CustomerMasterChangeReq, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)

    @api.model
    def create(self, vals):
        if vals.get('rec_no', _('New')) == _('New'):
            vals['rec_no'] = self.env['ir.sequence'].next_by_code(
                'customer.master.change.request') or _('New')
        res = super(CustomerMasterChangeReq, self).create(vals)
        return res

    def check_lines_changed(self, pricing_model):
        flag = 0
        new_record_flag = 0
        changes = {}
        if pricing_model == 'slab':
            if self.new_slab_pricing_plan_ids:
                for line in self.new_slab_pricing_plan_ids:
                    customer_slab_line_id = line.pricing_plan_id
                    if customer_slab_line_id:
                        if (line.from_distance == customer_slab_line_id.from_distance and
                                line.to_distance == customer_slab_line_id.to_distance and
                                line.minimum_weight == customer_slab_line_id.minimum_weight and
                                line.maximum_weight == customer_slab_line_id.maximum_weight and
                                line.price == customer_slab_line_id.price
                        ):
                            line.is_changed = False
                            if flag == 0:
                                flag = 0
                        else:
                            flag = 1
                            line.is_changed = True
                    else:
                        new_record_flag = 1
                changes.update({
                    'new_record_flag': new_record_flag,
                    'flag': flag
                })


            else:
                raise UserError('Please add pricing plan')


        elif pricing_model == 'KM':
            if self.new_km_pricing_plan_ids:
                for line in self.new_km_pricing_plan_ids:
                    customer_km_line_id = line.pricing_plan_id
                    if customer_km_line_id:
                        if (line.min_distance == customer_km_line_id.min_distance and
                                line.min_cost == customer_km_line_id.min_cost and
                                line.minimum_weight == customer_km_line_id.minimum_weight and
                                line.maximum_weight == customer_km_line_id.maximum_weight and
                                line.per_km_charge == customer_km_line_id.per_km_charge
                        ):
                            line.is_changed = False
                            if flag == 0:
                                flag = 0
                        else:
                            flag = 1
                            line.is_changed = True
                    else:
                        new_record_flag = 1

                changes.update({
                    'new_record_flag': new_record_flag,
                    'flag': flag
                })
            else:
                raise UserError('Please add pricing plan')

        elif pricing_model == 'flat':
            if self.new_flat_pricing_plan_ids:
                for line in self.new_flat_pricing_plan_ids:
                    customer_flat_line_id = line.pricing_plan_id

                    if customer_flat_line_id:
                        if (line.minimum_weight == customer_flat_line_id.minimum_weight and
                                line.maximum_weight == customer_flat_line_id.maximum_weight and
                                line.price == customer_flat_line_id.price
                        ):
                            line.is_changed = False
                            if flag == 0:
                                flag = 0
                        else:
                            flag = 1
                            line.is_changed = True
                    else:
                        new_record_flag = 1

                changes.update({
                    'new_record_flag': new_record_flag,
                    'flag': flag
                })
            else:
                raise UserError('Please add pricing plan')
        return changes

    def check_additional_charge_lines_changed(self, additional_charge_model):
        flag = 0
        changes = {}
        new_record_flag = 0
        if self.new_additional_charges_ids:
            charge_type_list = []
            for line in self.new_additional_charges_ids:
                charge_type_list.append(line.charge_type_id.name)
                additional_line_id = line.additional_charge_id
                if additional_line_id:
                    if (
                            additional_line_id.charge_type_id == line.charge_type_id and additional_line_id.amount_type == line.amount_type
                            and additional_line_id.amount == line.amount):
                        line.is_changed = False
                        if flag == 0:
                            flag = 0
                    else:
                        flag = 1
                        line.is_changed = True
                else:
                    new_record_flag = 1
            if charge_type_list:
                counter = Counter(charge_type_list)
                duplicates = [item for item, count in counter.items() if count > 1]
                if duplicates:
                    duplicate_charge_type = (', '.join(duplicates))
                    raise UserError(
                        _("In the additional charges section, the same charge types [%s] are added multiple times.Please remove the duplicates.") % (
                            duplicate_charge_type))

            changes.update({
                'new_record_flag': new_record_flag,
                'flag': flag
            })
        return changes

    def action_confirm(self):
        if self.comment:
            self.check_same_data()
            self.is_submitted = True
            self.update_user_action('New', 'Under UH Approval', self.comment)
            self.comment = False
            self.send_mail_user_submit()
            self.state = 'mu_approval_pending'
        else:
            form_view_id = self.env.ref('customer_master_change_request.customer_master_change_request_comment_form').id
            return {
                'name': _("Comment"),
                'view_type': 'form',
                'target': 'new',
                "view_mode": 'form',
                'res_model': 'customer.master.change.request',
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'view_id': form_view_id,
                'context': {
                    'val': 'user_submitted'}
            }

    def check_same_data(self):
        same_data = ''
        if self.is_address:
            if (self.street == self.customer_id.street and
                    self.city == self.customer_id.city and self.state_id == self.customer_id.state_id
                    and self.zip == self.customer_id.zip
                    and self.customer_id.zip and self.country_id == self.customer_id.country_id):
                same_data += 'Address,'
        if self.is_payment_mode and self.payment_mode_ids == self.customer_id.payment_mode_ids:
                same_data += 'Payment Mode,'
        if self.is_invoice_frequency_id and self.invoice_frequency_id == self.customer_id.invoice_frequency_id:
            same_data += 'Invoice Frequency,'
        if self.is_vat and self.vat == self.customer_id.vat:
            same_data += 'GSTIN,'
        if self.is_tax_id and self.l10n_in_pan == self.customer_id.l10n_in_pan:
            same_data += 'Pan,'
        if self.is_sms_alert and self.sms_alert == self.customer_id.sms_alert:
            same_data += 'Customer SMS Alert,'
        if self.is_email_alert and self.email_alert == self.customer_id.email_alert:
            same_data += 'Customer Email Alert,'
        if self.is_customer_segment_id and self.segment_id == self.customer_id.segment_id:
            same_data += 'Customer Segment,'
        if self.is_fleet_customer_segment_id and self.fleet_customer_segment_id == self.customer_id.segment_id:
            same_data += 'Customer Segment'
        if self.is_customer_type and self.customer_type == self.customer_id.customer_type:
            same_data += 'Customer Type,'
        if self.is_source_lead_type_id and self.source_lead_type_id == self.customer_id.source_lead_type_id:
            same_data += 'Source/Lead Type,'
        if self.is_potential_orders_id and self.potential_orders_id == self.customer_id.potential_orders_id:
            same_data += 'Potential Orders,'
        if self.is_industry_id and self.industry_id == self.customer_id.industry_id:
            same_data += 'Customer Industry,'
        if self.is_delivery_type_ids and self.delivery_type_id == self.customer_id.delivery_type_id:
            same_data += 'Type Of Delivery,'
        if self.is_pick_up_area and self.pick_up_area == self.customer_id.pick_up_area:
            same_data += 'Pick Up Area,'
        if self.is_pricing_type and self.pricing_type == self.customer_id.pricing_type:
            same_data += 'Pricing Type,'
        if self.is_tds and self.tds_threshold_check == self.customer_id.tds_threshold_check:
            same_data += 'TDS,'
        if self.is_item_category_id and self.item_category_id == self.customer_id.item_category_id:
            same_data += 'Item Category,'
        if self.is_order_sales_person and self.order_sales_person == self.customer_id.order_sales_person:
            same_data += 'Order Sales Person,'
        if self.is_api_selection and self.api_selection == self.customer_id.api_selection:
            same_data += 'API,'
        if self.is_distance_limitation and self.distance_limitation == self.customer_id.distance_limitation:
            same_data += 'Distance Limitation,'
        if self.is_followup_status_id and self.followup_status_id == self.customer_id.followup_status_id:
            same_data += 'Follow-up status,'
        if self.is_fleet_hsn_id and self.fleet_hsn_id == self.customer_id.fleet_hsn_id:
            same_data += 'Fleet HSN,'
        if self.is_credit_period_id and self.credit_period_id == self.customer_id.credit_period_id:
            same_data += 'Credit Period,'
        if self.is_contract_id and self.contract_id == self.customer_id.contract_id:
            same_data += 'Contract,'
        if self.is_contact_designation and self.contact_designation == self.customer_id.contact_designation:
            same_data += 'Contact Designation,'
        if self.is_product_line and self.product_line_id == self.customer_id.product_line_id:
            same_data += 'Product Lines,'
        if self.is_source and self.source_type_id == self.customer_id.source_type_id:
            same_data += 'Order Placement,'
        if self.is_fifo:
            if self.is_fifo_flow == self.customer_id.is_fifo_flow and self.max_no_de == self.customer_id.max_no_de:
                same_data += 'FIFO Flow,'
        if self.is_credit_limit:
            if self.active_limit == self.customer_id.active_limit and self.blocking_stage == self.customer_id.blocking_stage:
                same_data += 'Credit Limit,'
        if self.is_merchant_collection:
            if (self.merchant_amount_collection == self.customer_id.merchant_amount_collection) and (
                    self.amount_collection_limit == self.customer_id.amount_collection_limit) and (
                    self.collection_charges == self.customer_id.collection_charges) and (
                    self.settlement_time_id == self.customer_id.settlement_time_id):
                same_data += 'Merchant Collection,'
        # if self.is_credit_limit and self.active_limit and self.blocking_stage<=0.0:
        #     raise UserError(_("Credit Amount should be Greater than zero"))
        # if self.is_merchant_collection == True and self.merchant_amount_collection == 'yes' and self.amount_collection_limit <= 0.0:
        #     raise UserError(_("Merchant Amount Collection should be Greater than zero"))
        if self.is_price_plan:
            if self.pricing_model == 'slab':
                changes = self.check_lines_changed(self.pricing_model)
                if changes['flag'] == 0 and changes['new_record_flag'] == 0:
                    if len(self.new_slab_pricing_plan_ids) == len(self.previous_slab_pricing_plan_ids):
                        same_data += 'Slab Pricing Plan,'
            if self.pricing_model == 'KM':
                changes = self.check_lines_changed(self.pricing_model)
                if changes['flag'] == 0 and changes['new_record_flag'] == 0:
                    if len(self.new_km_pricing_plan_ids) == len(self.previous_km_pricing_plan_ids):
                        same_data += 'KM Pricing Plan,'
            if self.pricing_model == 'flat':
                changes = self.check_lines_changed(self.pricing_model)
                if changes['flag'] == 0 and changes['new_record_flag'] == 0:
                    if len(self.new_flat_pricing_plan_ids) == len(self.previous_flat_pricing_plan_ids):
                        same_data += 'Flat Pricing Plan,'
        if self.is_stop_charge:
            if self.new_additional_charges_ids:
                changes = self.check_additional_charge_lines_changed(self.new_additional_charges_ids)
                if changes['flag'] == 0 and changes['new_record_flag'] == 0:
                    if len(self.new_additional_charges_ids) == len(self.previous_additional_charges_ids):
                        same_data += 'Additional Charge'
            elif not self.new_additional_charges_ids and not self.previous_additional_charges_ids:
                same_data += 'Additional Charge'
        if not same_data == '':
            raise UserError("No Changes Reflected in Field {field}".format(field=same_data))
        if self.is_fifo_flow == 'yes' and self.max_no_de <= 0:
            raise UserError(_("Maximum Number of De should be Greater than zero"))
        if self.is_merchant_collection == True and self.merchant_amount_collection == 'yes' and self.amount_collection_limit <= 0.0:
            raise UserError(_("Merchant Amount Collection should be Greater than zero"))
        if self.is_credit_limit and self.active_limit and self.blocking_stage <= 0.0:
            raise UserError(_("Credit Amount should be Greater than zero"))



    def proceed_change_req(self):
        if not self.field_to_change:
            raise UserError('Please add the field to change')

        if not self.comment:
            form_view_id = self.env.ref('customer_master_change_request.customer_master_change_request_comment_form').id
            return {
                'name': _("Comment"),
                'view_type': 'form',
                'target': 'new',
                "view_mode": 'form',
                'res_model': 'customer.master.change.request',
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'view_id': form_view_id,
                'context': {'val': 'user_proceed'}
            }

        field_mapping = {
            '1': ('is_address', ['street', 'street2', 'zip', 'city', 'state_id', 'country_id']),
            '2': ('is_payment_mode',
                  ['payment_mode_ids', 'merchant_amount_collection', 'amount_collection_limit', 'collection_charges',
                   'settlement_time_id']),
            '3': ('is_invoice_frequency_id', ['invoice_frequency_id']),
            '4': ('is_vat', ['vat']),
            '5': ('is_customer_type', ['customer_type']),
            '6': ('is_tax_id', ['l10n_in_pan']),
            '7': ('is_sms_alert', ['sms_alert']),
            '8': ('is_email_alert', ['email_alert']),
            '9': ('is_customer_segment_id', ['segment_id']),
            '10': ('is_source_lead_type_id', ['source_lead_type_id']),
            '11': ('is_potential_orders_id', ['potential_orders_id']),
            '12': ('is_industry_id', ['industry_id']),
            '13': ('is_delivery_type_ids', ['delivery_type_id']),
            '14': ('is_pick_up_area', ['pick_up_area']),
            '15': ('is_pricing_type', ['pricing_type']),
            '16': ('is_item_category_id', ['item_category_id']),
            '17': ('is_price_plan', None),  # Special handling
            '18': ('is_order_sales_person', ['order_sales_person']),
            '19': ('is_api_selection', ['api_selection']),
            '20': ('is_distance_limitation', ['distance_limitation']),
            '21': ('is_followup_status_id', ['followup_status_id']),
            '22': ('is_fleet_hsn_id', ['fleet_hsn_id']),
            '23': ('is_credit_period_id', ['credit_period_id']),
            '24': ('is_contract_id', ['contract_id']),
            '25': ('is_contact_designation', ['contact_designation']),
            '26': ('is_fifo', ['max_no_de', 'is_fifo_flow']),
            '27': ('is_product_line', ['product_line_id']),
            '28': ('is_stop_charge', None),  # Special handling
            '29': ('is_source', ['source_type_id']),
            '30': ('is_fleet_customer_segment_id', None),
            '31': ('is_credit_limit', None),
            '32': ('is_merchant_collection', None),

        }

        for rec in self.field_to_change:
            code = rec.code
            if code == '26' and self.customer_type == 'b2c':
                raise UserError(_('Fifo flow is not available for retail customer.'))

            if code in field_mapping:
                flag_attr, fields_to_copy = field_mapping[code]
                setattr(self, flag_attr, True)

                if fields_to_copy:
                    for field in fields_to_copy:
                        setattr(self, field, getattr(self.customer_id, field))
            if code == '17':
                self._set_pricing_plan_details()
            if code == '30':
                self.is_fleet_customer_segment_id = True
                self.fleet_customer_segment_id = self.customer_id.segment_id.id
            if code == '28':
                self._set_additional_charges()
            if code == '31':
                self.active_limit = self.customer_id.active_limit
                self.blocking_stage = self.customer_id.blocking_stage
            if code == '32':
                self.merchant_amount_collection = self.customer_id.merchant_amount_collection
                self.amount_collection_limit = self.customer_id.amount_collection_limit
                self.amount_collection_sign = self.customer_id.amount_collection_sign
                self.settlement_time_id = self.customer_id.settlement_time_id.id
                self.collection_charges = self.customer_id.collection_charges
                self.collection_charges_sign = self.customer_id.collection_charges_sign
                self.collection_charges_sign = self.customer_id.collection_charges_sign

        self.is_proceed = True

    def _set_pricing_plan_details(self):
        self.is_price_plan = True
        if self.customer_id.pricing_model:
            self.pricing_model = self.customer_id.pricing_model
            self.previous_pricing_model = self.customer_id.pricing_model
        update_list = []
        if self.pricing_model == 'KM' and self.customer_id.km_pricing_plan_ids:
            for km_line in self.customer_id.km_pricing_plan_ids:
                km_line.previous_change_req_id = self.id
                update_list.append([0, 0, {
                    'minimum_weight': km_line.minimum_weight,
                    'maximum_weight': km_line.maximum_weight,
                    'min_distance': km_line.min_distance,
                    'min_cost': km_line.min_cost,
                    'per_km_charge': km_line.per_km_charge,
                    'select_plan_type': self.pricing_model,
                    'pricing_plan_id': km_line.id

                }])
            self.update({'new_km_pricing_plan_ids': update_list})
        if self.pricing_model == 'flat' and self.customer_id.flat_pricing_plan_ids:
            for flat_line in self.customer_id.flat_pricing_plan_ids:
                flat_line.previous_change_req_id = self.id
                update_list.append([0, 0, {
                    'minimum_weight': flat_line.minimum_weight,
                    'maximum_weight': flat_line.maximum_weight,
                    'price': flat_line.price,
                    'change_req_id': self.id,
                    'select_plan_type': self.pricing_model,
                    'pricing_plan_id': flat_line.id
                }])
            self.update({'new_slab_pricing_plan_ids': update_list})
        if self.pricing_model == 'slab' and self.customer_id.slab_pricing_plan_ids:
            for slab_line in self.customer_id.slab_pricing_plan_ids:
                slab_line.previous_change_req_id = self.id
                update_list.append([0, 0, {
                    'from_distance': slab_line.from_distance,
                    'to_distance': slab_line.to_distance,
                    'minimum_weight': slab_line.minimum_weight,
                    'maximum_weight': slab_line.maximum_weight,
                    'price': slab_line.price,
                    'select_plan_type': self.pricing_model,
                    'pricing_plan_id': slab_line.id

                }])
            self.update({'new_flat_pricing_plan_ids': update_list})

    def _set_additional_charges(self):
        """Handle copying of additional charges for stop charge."""
        additional_charge_list = []
        for charge_line in self.customer_id.additional_charges_ids:
            charge_line.previous_change_request_id = self.id
            additional_charge_list.append([0, 0, {
                'charge_type_id': charge_line.charge_type_id.id,
                'amount_type': charge_line.amount_type,
                'amount': charge_line.amount,
                'additional_charge_id': charge_line.id,
            }])
        self.update({'new_additional_charges_ids': additional_charge_list})

    def action_submit_form(self):
        ctx = self._context.get('val')
        if ctx == 'user_proceed' and self.comment:
            self.proceed_change_req()
        elif ctx == 'user_submitted' and self.comment:
            self.action_confirm()
        elif ctx == 'mu_approval' and self.comment:
            self.action_mu_approval()
        elif ctx == 'fn_mu_rejected' and self.comment:
            self.action_rejected()
        elif ctx == 'fin_approval' and self.comment:
            self.action_finance_approval()
        elif ctx == 'return_correction' and self.comment:
            self.action_return_correction()

    def action_rejected(self):
        if self.state in ['mu_approval_pending', 'fin_approval_pending']:
            if self.comment:
                if self.state == 'mu_approval_pending':
                    self.update_user_action('Under UH Approval', 'Rejected', self.comment)
                elif self.state == 'fin_approval_pending':
                    self.update_user_action('Under Finance Approval', 'Rejected', self.comment)
                self.rejected_mail_sending()
                self.state = 'rejected'
            else:
                form_view_id = self.env.ref(
                    'customer_master_change_request.customer_master_change_request_comment_form').id
                return {
                    'name': _("Comment"),
                    'view_type': 'form',
                    'target': 'new',
                    "view_mode": 'form',
                    'res_model': 'customer.master.change.request',
                    'res_id': self.id,
                    'type': 'ir.actions.act_window',
                    'view_id': form_view_id,
                    'context': {
                        'val': 'fn_mu_rejected'}
                }

    def action_mu_approval(self):
        self.check_same_data()
        if self.is_price_plan and not self.agreement_document:
            raise UserError("Agreement not found. Please upload the agreement.")
        if self.is_merchant_collection == True and self.merchant_amount_collection == 'yes' and self.amount_collection_limit <= 0.0:
            raise UserError(_("Merchant Amount Collection should be Greater than zero"))
        if self.state == 'mu_approval_pending' and self.comment:
            if self.is_price_plan:
                pricing_model = self.pricing_model
                self.check_lines_changed(pricing_model)
            if self.is_stop_charge and self.new_additional_charges_ids:
                self.check_additional_charge_lines_changed(self.new_additional_charges_ids)

            self.update_user_action('Under UH Approval', 'Under Finance Approval', self.comment)
            self.send_mu_to_fn_submit_mail()
            self.comment = False
            self.state = 'fin_approval_pending'
        else:
            form_view_id = self.env.ref('customer_master_change_request.customer_master_change_request_comment_form').id
            return {
                'name': _("Comment"),
                'view_type': 'form',
                'target': 'new',
                "view_mode": 'form',
                'res_model': 'customer.master.change.request',
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'view_id': form_view_id,
                'context': {
                    'val': 'mu_approval'}
            }

    def update_create_pricing_plan(self, pricing_model):
        if pricing_model == 'slab':
            slab_data = self.prepare_slab_pricing_plan_update()
            if slab_data.get('new_records'):
                self.customer_id.update({'slab_pricing_plan_ids': [(0, 0, rec) for rec in slab_data['new_records']]})
                for rec in slab_data['new_records']:
                    rec['updated_by'] = self.create_uid.id
                    rec['updated_date_time'] = datetime.now()
                    rec['select_plan_type'] = pricing_model
                    rec['action'] = 'New Pricing Line Added'
                    self.customer_id.update({'pricing_plan_update_log_ids': [(0, 0, rec)]})
            if slab_data.get('deleted_records'):
                data = {}
                for rec in slab_data['deleted_records']:
                    val = self.env['pricing.plan'].search([('id', '=', rec)])
                    data['updated_by'] = self.create_uid.id
                    data['updated_date_time'] = datetime.now()
                    data['select_plan_type'] = pricing_model
                    data['action'] = 'Pricing Line Deleted'
                    data['from_distance'] = val.from_distance
                    data['to_distance'] = val.to_distance
                    data['minimum_weight'] = val.minimum_weight
                    data['maximum_weight'] = val.maximum_weight
                    data['price'] = val.price
                    self.customer_id.update({'pricing_plan_update_log_ids': [(0, 0, data)]})
                    val.update({'partner_id': False})
            if slab_data.get('changed_records'):
                if slab_data.get('changed_slab_plan_records'):
                    update_log_list = []
                    for change_rec in slab_data['changed_slab_plan_records']:
                        change_data = []
                        if (change_rec.pricing_plan_id.minimum_weight != change_rec.minimum_weight or
                                change_rec.pricing_plan_id.maximum_weight != change_rec.maximum_weight):
                            if (change_rec.pricing_plan_id.maximum_weight != change_rec.maximum_weight and
                                    change_rec.pricing_plan_id.minimum_weight != change_rec.minimum_weight):
                                change_data.append('Min And Max  Weight(Kg) Bands')
                            elif change_rec.pricing_plan_id.minimum_weight != change_rec.minimum_weight:
                                change_data.append('Min Weight(Kg) Bands')
                            elif change_rec.pricing_plan_id.maximum_weight != change_rec.maximum_weight:
                                change_data.append('Max Weight(Kg) Bands')
                        if (change_rec.pricing_plan_id.from_distance != change_rec.from_distance or
                                change_rec.pricing_plan_id.to_distance != change_rec.to_distance):
                            if (change_rec.pricing_plan_id.from_distance != change_rec.from_distance and
                                    change_rec.pricing_plan_id.to_distance != change_rec.to_distance):
                                change_data.append('From And To Distance(Km)')
                            elif change_rec.pricing_plan_id.from_distance != change_rec.from_distance:
                                change_data.append('From Distance(Km) Bands')
                            elif change_rec.pricing_plan_id.to_distance != change_rec.to_distance:
                                change_data.append('To Distance(Km)')
                        if change_rec.pricing_plan_id.price != change_rec.price:
                            change_data.append('Price(Rs)')

                        update_log_list.append({
                            'minimum_weight': change_rec.pricing_plan_id.minimum_weight,
                            'maximum_weight': change_rec.pricing_plan_id.maximum_weight,
                            'from_distance': change_rec.pricing_plan_id.from_distance,
                            'to_distance': change_rec.pricing_plan_id.to_distance,
                            'price': change_rec.pricing_plan_id.price,
                            'partner_id': self.customer_id.id,
                            'updated_by': self.create_uid.id,
                            'updated_date_time': datetime.now(),
                            'select_plan_type': 'slab',
                            'action': ('{change_field} Are Updated'.format(change_field=','.join(change_data)) if len(
                                change_data) > 1 else '{change_field} Is Updated'.format(
                                change_field=','.join(change_data)))
                        })
                    self.customer_id.update({'pricing_plan_update_log_ids': [(0, 0, rec) for rec in update_log_list]})
                    self.customer_id.update({'slab_pricing_plan_ids': [rec for rec in slab_data['changed_records']]})

        if pricing_model == 'KM':
            km_data = self.prepare_km_pricing_plan_update()
            if km_data.get('new_records'):
                self.customer_id.update({'km_pricing_plan_ids': [(0, 0, rec) for rec in km_data['new_records']]})
                for rec in km_data['new_records']:
                    rec['updated_by'] = self.create_uid.id
                    rec['updated_date_time'] = datetime.now()
                    rec['select_plan_type'] = pricing_model
                    rec['action'] = 'New Pricing Line Added'
                    self.customer_id.update({'pricing_plan_update_log_ids': [(0, 0, rec)]})
            if km_data.get('deleted_records'):
                data = {}
                for rec in km_data['deleted_records']:
                    val = self.env['pricing.plan'].search([('id', '=', rec)])
                    data['updated_by'] = self.create_uid.id
                    data['updated_date_time'] = datetime.now()
                    data['select_plan_type'] = pricing_model
                    data['action'] = 'Pricing Line Deleted'
                    data['minimum_weight'] = val.minimum_weight
                    data['maximum_weight'] = val.maximum_weight
                    data['min_distance'] = val.min_distance
                    data['min_cost'] = val.min_cost
                    data['per_km_charge'] = val.per_km_charge
                    self.customer_id.update({'pricing_plan_update_log_ids': [(0, 0, data)]})
                    val.update({'partner_id': False})

            if km_data.get('changed_records'):
                if km_data.get('changed_km_plan_records'):
                    update_log_list = []
                    for change_rec in km_data['changed_km_plan_records']:
                        change_data = []
                        if (change_rec.pricing_plan_id.minimum_weight != change_rec.minimum_weight or
                                change_rec.pricing_plan_id.maximum_weight != change_rec.maximum_weight):
                            if (change_rec.pricing_plan_id.minimum_weight != change_rec.minimum_weight and
                                    change_rec.pricing_plan_id.maximum_weight != change_rec.maximum_weight):
                                change_data.append('From And To Weight Bands')
                            elif change_rec.pricing_plan_id.minimum_weight != change_rec.minimum_weight:
                                change_data.append('From Weight(Kg)')
                            elif change_rec.pricing_plan_id.maximum_weight != change_rec.maximum_weight:
                                change_data.append('From Weight(Kg)')
                        if change_rec.pricing_plan_id.min_distance != change_rec.min_distance:
                            change_data.append('Minimum Distance(Kg)')
                        if change_rec.pricing_plan_id.min_cost != change_rec.min_cost:
                            change_data.append('Minimum Cost(Rs)')
                        if change_rec.pricing_plan_id.per_km_charge != change_rec.per_km_charge:
                            change_data.append('Per Kilometer Charge(Rs)')
                        update_log_list.append({
                            'minimum_weight': change_rec.pricing_plan_id.minimum_weight,
                            'maximum_weight': change_rec.pricing_plan_id.maximum_weight,
                            'min_distance': change_rec.pricing_plan_id.min_distance,
                            'min_cost': change_rec.pricing_plan_id.min_cost,
                            'per_km_charge': change_rec.pricing_plan_id.per_km_charge,
                            'partner_id': self.customer_id.id,
                            'updated_by': self.create_uid.id,
                            'updated_date_time': datetime.now(),
                            'select_plan_type': 'KM',
                            'action': ('{change_field} Are Updated'.format(change_field=','.join(change_data)) if len(
                                change_data) > 1 else '{change_field} Is Updated'.format(
                                change_field=','.join(change_data)))
                        })
                    self.customer_id.update({'pricing_plan_update_log_ids': [(0, 0, rec) for rec in update_log_list]})
                    self.customer_id.update({'km_pricing_plan_ids': [rec for rec in km_data['changed_records']]})

        if pricing_model == 'flat':
            flat_data = self.prepare_flat_pricing_plan_update()
            if flat_data.get('new_records'):
                self.customer_id.update({'flat_pricing_plan_ids': [(0, 0, rec) for rec in flat_data['new_records']]})
                for rec in flat_data['new_records']:
                    rec['updated_by'] = self.create_uid.id
                    rec['updated_date_time'] = datetime.now()
                    rec['select_plan_type'] = pricing_model
                    rec['action'] = 'New Pricing Line Added'
                    self.customer_id.update({'pricing_plan_update_log_ids': [(0, 0, rec)]})
            if flat_data.get('deleted_records'):
                data = {}
                for rec in flat_data['deleted_records']:
                    val = self.env['pricing.plan'].search([('id', '=', rec)])
                    data['updated_by'] = self.create_uid.id
                    data['updated_date_time'] = datetime.now()
                    data['select_plan_type'] = pricing_model
                    data['action'] = 'Pricing Line Deleted'
                    data['minimum_weight'] = val.minimum_weight
                    data['maximum_weight'] = val.maximum_weight
                    data['price'] = val.price
                    self.customer_id.update({'pricing_plan_update_log_ids': [(0, 0, data)]})
                    val.update({'partner_id': False})
            if flat_data.get('changed_records'):
                if flat_data.get('changed_flat_plan_records'):
                    update_log_list = []
                    for change_rec in flat_data['changed_flat_plan_records']:
                        change_data = []
                        if (change_rec.pricing_plan_id.minimum_weight != change_rec.minimum_weight or
                                change_rec.pricing_plan_id.maximum_weight != change_rec.maximum_weight):
                            if (change_rec.pricing_plan_id.minimum_weight != change_rec.minimum_weight and
                                    change_rec.pricing_plan_id.maximum_weight != change_rec.maximum_weight):
                                change_data.append('Min And Max Weight Bands')
                            elif change_rec.pricing_plan_id.minimum_weight != change_rec.minimum_weight:
                                change_data.append('Min Weight(Kg)')
                            elif change_rec.pricing_plan_id.maximum_weight != change_rec.maximum_weight:
                                change_data.append('Max Weight(Kg)')
                        if change_rec.pricing_plan_id.price != change_rec.price:
                            change_data.append('Price(kg)')
                        update_log_list.append({
                            'minimum_weight': change_rec.pricing_plan_id.minimum_weight,
                            'maximum_weight': change_rec.pricing_plan_id.maximum_weight,
                            'price': change_rec.pricing_plan_id.price,
                            'partner_id': self.customer_id.id,
                            'updated_by': self.create_uid.id,
                            'updated_date_time': datetime.now(),
                            'select_plan_type': 'flat',
                            'action': ('{change_field} Are Updated'.format(change_field=','.join(change_data)) if len(
                                change_data) > 1 else '{change_field} Is Updated'.format(
                                change_field=','.join(change_data)))
                        })
                    self.customer_id.update(
                        {'pricing_plan_update_log_ids': [(0, 0, rec) for rec in update_log_list]})
                    self.customer_id.update({'flat_pricing_plan_ids': [rec for rec in flat_data['changed_records']]})
        if self.agreement_document:
            self.customer_id.update(
                {'document_ids': [(0, 0, {
                    'document_name': 'Agreement',
                    'file': self.agreement_document})]
                 }
            )
        self._update_customer_pricing_model_plan_and_log(pricing_model)

    def prepare_slab_pricing_plan_update(self):
        update_dict = {}
        if self.pricing_model == 'slab' and self.new_slab_pricing_plan_ids:
            deleted_records = self.mapped('previous_slab_pricing_plan_ids') - self.new_slab_pricing_plan_ids.mapped(
                'pricing_plan_id')
            new_records = self.env['pricing.plan'].search(
                [('change_req_id', '=', self.id), ('pricing_plan_id', '=', False)])
            changed_records = self.env['pricing.plan'].search(
                [('is_changed', '=', True), ('change_req_id', '=', self.id)])
            if deleted_records:
                update_dict['deleted_records'] = [rec.id for rec in deleted_records]
            if changed_records:
                change_list = []
                for rec in changed_records:
                    change_list.append((1, rec.pricing_plan_id.id, {
                        'from_distance': rec.from_distance,
                        'to_distance': rec.to_distance,
                        'minimum_weight': rec.minimum_weight,
                        'maximum_weight': rec.maximum_weight,
                        'price': rec.price,
                        'select_plan_type': self.pricing_model,

                    }))
                update_dict['changed_records'] = change_list
                update_dict['changed_slab_plan_records'] = changed_records

            if new_records:
                new_record_list = []
                for rec in new_records:
                    new_record_list.append({
                        'from_distance': rec.from_distance,
                        'to_distance': rec.to_distance,
                        'minimum_weight': rec.minimum_weight,
                        'maximum_weight': rec.maximum_weight,
                        'price': rec.price,
                        'select_plan_type': self.pricing_model,
                        'partner_id': self.customer_id.id,
                    })
                update_dict['new_records'] = new_record_list

            return update_dict

    def prepare_km_pricing_plan_update(self):
        update_dict = {}
        crm_lead = self.env['crm.lead'].search([('partner_id', '=', self.customer_id.id)])
        if self.pricing_model == 'KM' and self.new_km_pricing_plan_ids:
            deleted_records = self.mapped('previous_km_pricing_plan_ids') - self.new_km_pricing_plan_ids.mapped(
                'pricing_plan_id')
            new_records = self.env['pricing.plan'].search(
                [('change_req_id', '=', self.id), ('pricing_plan_id', '=', False)])
            changed_records = self.env['pricing.plan'].search(
                [('is_changed', '=', True), ('change_req_id', '=', self.id)])
            if deleted_records:
                update_dict['deleted_records'] = [rec.id for rec in deleted_records]
            if changed_records:
                change_list = []
                for rec in changed_records:
                    change_list.append((1, rec.pricing_plan_id.id, {
                        'min_distance': rec.min_distance,
                        'min_cost': rec.min_cost,
                        'minimum_weight': rec.minimum_weight,
                        'maximum_weight': rec.maximum_weight,
                        'per_km_charge': rec.per_km_charge,
                        'select_plan_type': rec.select_plan_type or False,
                        'partner_id': self.customer_id.id,

                    }))
                update_dict['changed_records'] = change_list
                update_dict['changed_km_plan_records'] = changed_records

            if new_records:
                new_record_list = []
                for rec in new_records:
                    new_record_list.append({
                        'min_distance': rec.min_distance,
                        'min_cost': rec.min_cost,
                        'minimum_weight': rec.minimum_weight,
                        'maximum_weight': rec.maximum_weight,
                        'per_km_charge': rec.per_km_charge,
                        'select_plan_type': rec.select_plan_type or False,
                        'partner_id': self.customer_id.id,
                    })
                update_dict['new_records'] = new_record_list
            return update_dict

    def prepare_flat_pricing_plan_update(self):
        update_dict = {}
        if self.pricing_model == 'flat' and self.new_flat_pricing_plan_ids:
            deleted_records = self.mapped('previous_flat_pricing_plan_ids') - self.new_flat_pricing_plan_ids.mapped(
                'pricing_plan_id')
            new_records = self.env['pricing.plan'].search(
                [('change_req_id', '=', self.id), ('pricing_plan_id', '=', False)])
            changed_records = self.env['pricing.plan'].search(
                [('is_changed', '=', True), ('change_req_id', '=', self.id)])
            if deleted_records:
                update_dict['deleted_records'] = [rec.id for rec in deleted_records]
            if changed_records:
                change_list = []
                for rec in changed_records:
                    change_list.append((1, rec.pricing_plan_id.id, {
                        'minimum_weight': rec.minimum_weight,
                        'maximum_weight': rec.maximum_weight,
                        'price': rec.price,
                        'select_plan_type': rec.select_plan_type or False,
                    }))
                update_dict['changed_records'] = change_list
                update_dict['changed_flat_plan_records'] = changed_records

            if new_records:
                new_record_list = []
                for rec in new_records:
                    new_record_list.append({
                        'minimum_weight': rec.minimum_weight,
                        'maximum_weight': rec.maximum_weight,
                        'price': rec.price,
                        'select_plan_type': self.pricing_model,
                        'partner_id': self.customer_id.id,
                    })
                update_dict['new_records'] = new_record_list
            return update_dict

    def _update_customer_pricing_model_plan_and_log(self, pricing_model):
        if pricing_model == 'KM':
            pricing_plan = self.env['pricing.plan'].search(
                [('partner_id', '=', self.customer_id.id), ('select_plan_type', 'in', ['slab', 'flat'])])
            for plan in pricing_plan:
                self.customer_id.update({'pricing_plan_update_log_ids': [(0, 0, {
                    'minimum_weight': plan.minimum_weight,
                    'maximum_weight': plan.minimum_weight,
                    'from_distance': plan.from_distance,
                    'to_distance': plan.to_distance,
                    'price': plan.price,
                    'min_cost': plan.min_cost,
                    'per_km_charge': plan.per_km_charge,
                    'partner_id': self.customer_id.id,
                    'updated_by': self.create_uid.id,
                    'updated_date_time': self.create_date,
                    'select_plan_type': 'slab',
                    'action': 'Pricing Plan Changed To KM'
                })]})
                plan.partner_id = False
        elif pricing_model == 'slab':
            pricing_plan = self.env['pricing.plan'].search(
                [('partner_id', '=', self.customer_id.id), ('select_plan_type', 'in', ['KM', 'flat'])])
            for plan in pricing_plan:
                self.customer_id.update({'pricing_plan_update_log_ids': [(0, 0, {
                    'minimum_weight': plan.minimum_weight,
                    'maximum_weight': plan.minimum_weight,
                    'from_distance': plan.from_distance,
                    'to_distance': plan.to_distance,
                    'price': plan.price,
                    'min_cost': plan.min_cost,
                    'per_km_charge': plan.per_km_charge,
                    'partner_id': self.customer_id.id,
                    'updated_by': self.create_uid.id,
                    'updated_date_time': self.create_date,
                    'select_plan_type': 'slab',
                    'action': 'Pricing Plan Changed To Slab'
                })]})
                plan.partner_id = False
        elif pricing_model == 'flat':
            pricing_plan = self.env['pricing.plan'].search(
                [('partner_id', '=', self.customer_id.id), ('select_plan_type', 'in', ['KM', 'slab'])])
            for plan in pricing_plan:
                self.customer_id.update({'pricing_plan_update_log_ids': [(0, 0, {
                    'minimum_weight': plan.minimum_weight,
                    'maximum_weight': plan.minimum_weight,
                    'from_distance': plan.from_distance,
                    'to_distance': plan.to_distance,
                    'price': plan.price,
                    'min_cost': plan.min_cost,
                    'per_km_charge': plan.per_km_charge,
                    'partner_id': self.customer_id.id,
                    'updated_by': self.create_uid.id,
                    'updated_date_time': self.create_date,
                    'select_plan_type': 'slab',
                    'action': 'Pricing Plan Changed To Flat'
                })]})
                plan.partner_id = False

    def prepare_pricing_plan_data(self):
        update_dict = {}
        deleted_records = self.mapped('previous_km_pricing_plan_ids') - self.new_km_pricing_plan_ids.mapped(
            'pricing_plan_id')
        new_records = self.env['pricing.plan'].search(
            [('change_req_id', '=', self.id), ('pricing_plan_id', '=', False)])
        changed_records = self.env['pricing.plan'].search(
            [('is_changed', '=', True), ('change_req_id', '=', self.id)])
        if deleted_records:
            update_dict['deleted_records'] = [rec.id for rec in deleted_records]
        if changed_records:
            change_list = []
            for rec in changed_records:
                change_list.append((1, rec.pricing_plan_id.id, {
                    'minimum_weight': rec.minimum_weight or False,
                    'maximum_weight': rec.maximum_weight or False,
                    'min_distance': rec.min_distance or False,
                    'min_cost': rec.min_cost or False,
                    'per_km_charge': rec.per_km_charge or False,
                    'from_distance': rec.from_distance or False,
                    'to_distance': rec.to_distance or False,
                    'price': rec.price or False,
                    'select_plan_type': rec.select_plan_type or False,

                }))
            update_dict['changed_records'] = change_list
            update_dict['changed_slab_plan_records'] = changed_records
        if new_records:
            new_record_list = []
            for rec in new_records:
                new_record_list.append({
                    'minimum_weight': rec.minimum_weight or False,
                    'maximum_weight': rec.maximum_weight or False,
                    'min_distance': rec.min_distance or False,
                    'min_cost': rec.min_cost or False,
                    'per_km_charge': rec.per_km_charge or False,
                    'from_distance': rec.from_distance or False,
                    'to_distance': rec.to_distance or False,
                    'price': rec.price or False,
                    'partner_id': self.customer_id.id,
                    'select_plan_type': rec.select_plan_type or False,
                })
            update_dict['new_records'] = new_record_list
        return update_dict

    def update_create_additional_charge(self, pricing_model, delete_table):
        additional_charge_data = self.prepare_additional_charge_update(delete_table)
        if additional_charge_data.get('new_records'):
            self.customer_id.update(
                {'additional_charges_ids': [(0, 0, rec) for rec in additional_charge_data['new_records']]})
            for rec in additional_charge_data['new_records']:
                rec['updated_by'] = self.create_uid.id
                rec['updated_date_time'] = datetime.now()
                rec['action'] = 'New Additional Charge Added'
                self.customer_id.update({'additional_charge_update_log_ids': [(0, 0, rec)]})
        if additional_charge_data.get('deleted_records'):
            data = {}
            for rec in additional_charge_data['deleted_records']:
                val = self.env['customer.additional.charges'].search([('id', '=', rec)])
                data['updated_by'] = self.create_uid.id
                data['updated_date_time'] = datetime.now()
                data['action'] = 'Pricing Line Deleted'
                data['charge_type_id'] = val.charge_type_id.id
                data['amount_type'] = val.amount_type
                data['amount'] = val.amount
                self.customer_id.update({'additional_charge_update_log_ids': [(0, 0, data)]})
                val.update({'partner_id': False})
        if additional_charge_data.get('changed_records'):
            if additional_charge_data['changed_additional_charge_records']:
                update_log_list = []
                for change_rec in additional_charge_data['changed_additional_charge_records']:
                    change_data = []
                    if change_rec.additional_charge_id.charge_type_id != change_rec.charge_type_id:
                        change_data.append('Charge Type')
                    if change_rec.additional_charge_id.amount_type != change_rec.amount_type:
                        change_data.append('Amount Type')
                    if change_rec.additional_charge_id.amount != change_rec.amount_type:
                        change_data.append('Amount/Percentage')

                    update_log_list.append({
                        'charge_type_id': change_rec.additional_charge_id.charge_type_id.id,
                        'amount_type': change_rec.additional_charge_id.amount_type,
                        'amount': change_rec.additional_charge_id.amount,
                        'partner_id': self.customer_id.id,
                        'updated_by': self.create_uid.id,
                        'updated_date_time': datetime.now(),
                        'action': ('{change_field} Are Updated'.format(change_field=','.join(change_data)) if len(
                            change_data) > 1 else '{change_field} Is Updated'.format(
                            change_field=','.join(change_data)))
                    })
                self.customer_id.update({'additional_charge_update_log_ids': [(0, 0, rec) for rec in update_log_list]})
                self.customer_id.update(
                    {'additional_charges_ids': [rec for rec in additional_charge_data['changed_records']]})

    def prepare_additional_charge_update(self, delete=None):
        update_dict = {}
        # crm_lead = self.env['crm.lead'].search([('partner_id', '=', self.customer_id.id)])
        if self.new_additional_charges_ids and not delete:
            deleted_records = self.mapped(
                'previous_additional_charges_ids') - self.new_additional_charges_ids.mapped(
                'additional_charge_id')
            new_records = self.env['customer.additional.charges'].search(
                [('change_request_id', '=', self.id), ('additional_charge_id', '=', False)])
            changed_records = self.env['customer.additional.charges'].search(
                [('is_changed', '=', True), ('change_request_id', '=', self.id)])
            if deleted_records:
                update_dict['deleted_records'] = [rec.id for rec in deleted_records]
            if changed_records:
                change_list = []
                for rec in changed_records:
                    change_list.append((1, rec.additional_charge_id.id, {
                        'charge_type_id': rec.charge_type_id.id,
                        'amount_type': rec.amount_type,
                        'amount': rec.amount,
                    }))
                update_dict['changed_records'] = change_list
                update_dict['changed_additional_charge_records'] = changed_records

            if new_records:
                new_record_list = []
                for rec in new_records:
                    new_record_list.append({
                        'charge_type_id': rec.charge_type_id.id,
                        'amount_type': rec.amount_type,
                        'amount': rec.amount,
                        'partner_id': self.customer_id.id,
                    })
                update_dict['new_records'] = new_record_list


        else:
            deleted_records = self.customer_id.mapped('additional_charges_ids')
            if deleted_records:
                update_dict['deleted_records'] = [rec.id for rec in deleted_records]

        return update_dict

    def action_finance_approval(self):
        self.check_same_data()
        if self.is_price_plan and not self.agreement_document:
            raise UserError("Agreement not found. Please upload the agreement.")
        update_data = self.prepare_update_data()
        if update_data and self.comment:
            if update_data.get('pricing_model') and self.is_price_plan:
                pricing_model = update_data['pricing_model']
                self.check_lines_changed(pricing_model)
                self.update_create_pricing_plan(pricing_model)
            if self.is_stop_charge:
                update_data.pop('is_stop_charge', None)
                if self.new_additional_charges_ids:
                    self.check_additional_charge_lines_changed(self.new_additional_charges_ids)
                    self.update_create_additional_charge(self.new_additional_charges_ids, delete_table=False)
                elif self.prepare_additional_charge_update():
                    update_data.pop('is_stop_charge', None)
                    self.update_create_additional_charge(self.new_additional_charges_ids, delete_table=True)
            if update_data:
                self.customer_id.update(update_data)
            update_log = {
                'partner_id': self.customer_id.id,
                'created_by': self.create_uid.id,
                'date_time': datetime.now(),
                'change_request_id': self.id
            }
            log = self.env['customer.update.log'].create(update_log)
            if log:
                self.customer_id.update({'customer_update_log_ids': [(4, 0), log]})
            self.update_user_action('Under Finance Approval', 'Approved', self.comment)
            self.state = 'approved'
        else:
            form_view_id = self.env.ref('customer_master_change_request.customer_master_change_request_comment_form').id
            return {
                'name': _("Comment"),
                'view_type': 'form',
                'target': 'new',
                "view_mode": 'form',
                'res_model': 'customer.master.change.request',
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'view_id': form_view_id,
                'context': {
                    'val': 'fin_approval'}
            }
        return update_data,update_log

    # Prepare data for updating the customer master

    def prepare_update_data(self):
        data = {}
        if self.is_address:
            data.update({
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state_id': self.state_id,
                'zip': self.zip,
                'country_id': self.country_id,
            })
        if self.is_payment_mode and self.payment_mode_ids:
            payment_mode_list = []
            self.customer_id.payment_mode_ids = False
            for payment_mode in self.payment_mode_ids:
                payment_mode_list.append(payment_mode)
            data.update({'payment_mode_ids': [(4, payment_mode.id) for payment_mode in payment_mode_list],
                         })
        if self.is_merchant_collection:
            if self.merchant_amount_collection == 'yes':
                data.update({
                    'merchant_amount_collection': self.merchant_amount_collection,
                    'amount_collection_limit': self.amount_collection_limit,
                    'settlement_time_id': self.settlement_time_id,
                    'collection_charges': self.collection_charges
                })
            else:
                data.update({
                    'merchant_amount_collection': self.merchant_amount_collection,
                    'amount_collection_limit': False,
                    'settlement_time_id': False,
                    'collection_charges': False
                })
        if self.is_invoice_frequency_id and self.invoice_frequency_id:
            data.update({
                'invoice_frequency_id': self.invoice_frequency_id
            })
        if self.is_vat and self.vat:
            data.update({'vat': self.vat})
        if self.is_customer_type and self.customer_type:
            data.update({'customer_type': self.customer_type})
        if self.is_tax_id and self.l10n_in_pan:
            data.update({'l10n_in_pan': self.l10n_in_pan})
        if self.is_sms_alert and self.sms_alert:
            data.update({'sms_alert': self.sms_alert})
        if self.is_email_alert and self.email_alert:
            data.update({'email_alert': self.email_alert})
        if self.is_customer_segment_id and self.segment_id:
            data.update({'segment_id': self.segment_id})
        if self.is_fleet_customer_segment_id and self.fleet_customer_segment_id:
            data.update({'segment_id': self.fleet_customer_segment_id})
        if self.is_source_lead_type_id and self.source_lead_type_id:
            data.update({'source_lead_type_id': self.source_lead_type_id})
        if self.is_industry_id and self.industry_id:
            data.update({'industry_id': self.industry_id})
        if self.is_potential_orders_id and self.potential_orders_id:
            data.update({'potential_orders_id': self.potential_orders_id})
        if self.is_delivery_type_ids and self.delivery_type_id:
            data.update({'delivery_type_id': self.delivery_type_id})
        if self.is_pick_up_area and self.pick_up_area:
            data.update({'pick_up_area': self.pick_up_area})
        if self.is_pricing_type and self.pricing_type:
            data.update({'pricing_type': self.pricing_type})
        if self.is_tds and self.tds_threshold_check:
            data.update({'tds_threshold_check': self.tds_threshold_check})
        if self.is_item_category_id and self.item_category_id:
            data.update({'item_category_id': self.item_category_id})
        if self.is_price_plan:
            data.update({'pricing_model': self.pricing_model})
        if self.is_order_sales_person and self.order_sales_person:
            data.update({'order_sales_person': self.order_sales_person})
        if self.is_api_selection and self.api_selection:
            data.update({'api_selection': self.api_selection})
        if self.is_distance_limitation and self.distance_limitation:
            data.update({'distance_limitation': self.distance_limitation})
        if self.is_followup_status_id and self.followup_status_id:
            data.update({'followup_status_id': self.followup_status_id})
        if self.is_fleet_hsn_id and self.fleet_hsn_id:
            data.update({'fleet_hsn_id': self.fleet_hsn_id})
        if self.is_credit_period_id and self.credit_period_id:
            data.update({'credit_period_id': self.credit_period_id})
        if self.is_contract_id and self.contract_id:
            data.update({'contract_id': self.contract_id})
        if self.is_contact_designation and self.contact_designation:
            data.update({'contact_designation': self.contact_designation})
        if self.is_fifo and self.is_fifo_flow:
            data.update({'is_fifo_flow': self.is_fifo_flow})
            data.update({'max_no_de': self.max_no_de})
        if self.is_stop_charge:
            data.update({'is_stop_charge': self.is_stop_charge})
        if self.is_product_line and self.product_line_id:
            data.update({'product_line_id': self.product_line_id})
        if self.is_source and self.source_type_id:
            data.update({'source_type_id': self.source_type_id})
        if self.is_price_plan:
            data.update({'pricing_model': self.pricing_model})
        if self.is_credit_limit:
            if self.active_limit:
                data.update({'blocking_stage': self.blocking_stage,
                             'active_limit':self.active_limit})
            else:
                data.update({'blocking_stage': 0.0,
                             'active_limit': self.active_limit})
        return data

    def action_return_correction(self):
        if self.state == 'mu_approval_pending' and self.comment:
            self.update_user_action('Under MU Approval', 'New', self.comment)
            self.comment = False
            self.state = 'new'
        elif self.state == 'fin_approval_pending' and self.comment:
            self.update_user_action('Under Finance Approval', 'Under MU Approval', self.comment)
            self.comment = False
            self.return_correction_mail_sending()
            self.state = 'mu_approval_pending'
        else:
            form_view_id = self.env.ref('customer_master_change_request.customer_master_change_request_comment_form').id
            return {
                'name': _("Comment"),
                'view_type': 'form',
                'target': 'new',
                "view_mode": 'form',
                'res_model': 'customer.master.change.request',
                'res_id': self.id,
                'type': 'ir.actions.act_window',
                'view_id': form_view_id,
                'context': {
                    'val': 'return_correction'}
            }

    def update_user_action(self, state_from, state_to, comment):
        lines = []
        state_f = state_from
        state_t = state_to
        current_user = self.env.user
        if comment:
            vals = {
                'state_from': state_f,
                'state_to': state_t,
                'res_user': current_user.id,
                'comments': comment
            }
            lines.append((0, 0, vals))
            self.user_action_ids = lines

    @api.model
    def get_email_to(self):
        req_created_user = self.create_uid
        current_user = self.env.user
        send_mail = ''
        if self.state == 'fin_approval_pending':
            employee_id = self.env['hr.employee'].search([('user_id', '=', req_created_user.id)])
            employee_mu_id = employee_id.mu_id
            send_mail = employee_mu_id.user_id.email
        if self.state == 'mu_approval_pending':
            send_mail = req_created_user.email
        if self.state == 'new':
            employee_id = self.env['hr.employee'].search([('user_id', '=', current_user.id)])
            employee_mu_id = employee_id.mu_id
            send_mail = employee_mu_id.user_id.email
        return send_mail

    @api.model
    def reject_email_to(self):
        req_created_user = self.create_uid
        send_mail_list = []
        if self.state == 'fin_approval_pending':
            send_mail_list.append(req_created_user.email)
            employee_id = self.env['hr.employee'].search([('user_id', '=', req_created_user.id)])
            employee_mu_id = employee_id.mu_id
            if employee_mu_id:
                send_mail_list.append(employee_mu_id.user_id.email)
            return ",".join(send_mail_list)
        if self.state == 'mu_approval_pending':
            send_mail = req_created_user.email
            return send_mail

    def send_mail_user_submit(self):
        template = self.env.ref('customer_master_change_request.change_req_user_to_mu_temp')
        template.send_mail(self.id, force_send=True)

    def send_mu_to_fn_submit_mail(self):
        template = self.env.ref('customer_master_change_request.change_req_mu_to_finance_temp')
        template.send_mail(self.id, force_send=True)

    def rejected_mail_sending(self):
        template = self.env.ref('customer_master_change_request.change_req_reject_temp')
        template.send_mail(self.id, force_send=True)

    def return_correction_mail_sending(self):
        template = self.env.ref('customer_master_change_request.change_req_return_correction_temp')
        template.send_mail(self.id, force_send=True)

    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id


    @api.onchange('fleet_customer_segment_id')
    def onchange_fleet_customer_segment(self):
        if self.fleet_customer_segment_id:
            if self.fleet_customer_segment_id.is_ftl and self.customer_id.segment_id.is_ftl != True:
                self.is_contact_designation = True
                if self.customer_id.contact_designation:
                    self.contact_designation = self.customer_id.contact_designation
                    self.customer_id.contact_designation = False
                self.is_credit_period_id = True
                if self.customer_id.credit_period_id:
                    self.credit_period_id = self.customer_id.credit_period_id.id
                    self.customer_id.credit_period_id = False
            else:
                self.is_contract_id = False
                self.contract_id = False
                self.is_contact_designation = False
                self.contact_designation = False
                self.is_credit_period_id = False
                self.credit_period_id = False
