# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo import SUPERUSER_ID
from lxml import etree

LEAD_STATE = [
    ("new", "New"),
    ("pending_approval", "Pending Approval"),
    ("manager_approve", "Manager Approved"),
    ("finance_approve", "Finance Approved"),
    ("reject", "Rejected")
]


class VendorLead(models.Model):
    """This model contains to onboard new vendors """
    _name = 'vendor.lead'
    _description = 'Vendor Lead'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    
    
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(VendorLead, self).get_view(view_id=view_id, view_type=view_type, **options)
        doc = etree.XML(res['arch'])
        
        if not self.env.user.has_group('vendor_onboarding.group_vendor_onboarding_create_access'):           
            if view_type == 'tree':
                for node_form in doc.xpath("//tree"):
                    node_form.set("create", 'false')
            if view_type == 'kanban':
                for node_form in doc.xpath("//kanban"):
                    node_form.set("create", 'false')
            if view_type == 'form':
                for node_form in doc.xpath("//form"):
                    node_form.set("create", 'false')
                    
        if not self.env.user.has_group('vendor_onboarding.group_vendor_onboarding_edit'):
            if view_type == 'form':
                for node_form in doc.xpath("//form"):
                    node_form.set("edit", 'false')
                    
        
        res['arch'] = etree.tostring(doc)
        return res
    
    
    # ONBOARDING Form
    name = fields.Char(string='Name')
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    city = fields.Char(string='City')
    state_id = fields.Many2one(comodel_name='res.country.state', string='State')
    zip = fields.Char(string='Zip')
    country_id = fields.Many2one(comodel_name='res.country', string='Country',
                                 default=lambda self: self.env.company.country_id)
    vat = fields.Char(string='GSTIN')
    region_id = fields.Many2one(comodel_name='sales.region', string='Region', domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    email = fields.Char(string='Email')
    service_type_id = fields.Many2one(comodel_name='partner.service.type', string='Service Type')
    segment_id = fields.Many2one(comodel_name="partner.segment", string="Segment",required=1)
    state = fields.Selection(LEAD_STATE, string='Status', default=LEAD_STATE[0][0], group_expand='_expand_groups',
                             copy=False, tracking=True)
    country_code = fields.Char("Code", default="+91")
    virtual_bank_acc = fields.Char(string='Virtual Bank Account')
    pan = fields.Char(string='PAN')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    #New Vendor
    partner_id = fields.Many2one('res.partner', string='Vendor', copy=False,
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    # Approved User
    approved_users = fields.Json(string='Approved User', copy=False)
    # User Action History
    user_action_ids = fields.One2many('vendor.lead.user.action.history', 'vendor_lead_id', string='User Action',
                                      copy=False)
    # Edit Access
    is_editable = fields.Boolean(string='Is Editable?', compute='_compute_is_editable', default=True, copy=False)
    # Bank Details
    account_no = fields.Char(string='Account No')
    ifsc_code = fields.Char(string='IFSC Code')
    bank_name = fields.Char(string='Bank Name')
    # Documents Details
    document_ids = fields.One2many('vendor.lead.document.line', 'vendor_lead_id', 'Documents')
    # TDS
    tax_tds_id = fields.Many2one('account.tax', string="TDS", domain=[('is_tds', '=', True)])

    _sql_constraints = [
        ('phone_numeric', 'CHECK(phone ~ \'^[0-9]{10}$\')',
         'Invalid characters or phone number must be 10 digits !'),
        ('mobile_numeric', 'CHECK(mobile ~ \'^[0-9]{10}$\')',
         'Invalid characters or mobile number must be 10 digits !'),
    ]

    @api.model
    def _expand_groups(self, states, domain, order):
        """to order status in kanban view"""
        return ['new', 'pending_approval', 'manager_approve', 'finance_approve', 'reject']

    def check_phone_no(self, phone, string):
        vendor_phone = self.env['vendor.lead'].search(
            ['|', ('phone', '=', phone), ('mobile', '=', phone), ('id', '!=', self._origin.id)]) or False
        if vendor_phone:
            vendors_phone = ','.join(vendor_phone.mapped('name'))
            raise UserError(_('%s No already Exist in %s.' % (string, vendors_phone)))
        phone = "+91" + phone
        partner_phone = self.env['res.partner'].search(
            ['|', ('phone', '=', phone), ('mobile', '=', phone)]) or False
        if partner_phone:
            partners_phone = ','.join(partner_phone.mapped('name'))
            raise UserError(_('%s No already Exist in %s.' % (string, partners_phone)))

    @api.constrains('phone', 'mobile')
    def _check_phone_no(self):
        """
        Onchange phone or mobile: Checking phone or mobile is already used or not.
        """
        for rec in self:
            if rec.phone:
                rec.check_phone_no(rec.phone, 'Phone')

            if rec.mobile:
                rec.check_phone_no(rec.mobile, 'Mobile')

    def unlink(self):
        for rec in self:
            if rec.state not in ('new', 'reject'):
                raise UserError(_("You cannot delete the record when it is not in 'new' or 'rejected' state."))
        return super(VendorLead, self).unlink()

    def action_approve_comment(self):
        for rec in self:
            """
            Button Action. User action comment wizard is opened when clicked on this and related 
            context is passed as True through this.
            """
            state = False
            if self.env.context.get('from_send_for_approve', False):
                if rec.state != 'new':
                    state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
            elif self.env.context.get('from_manager_approve', False) or rec._context.get('button_manager_user', False):
                if rec.state != 'pending_approval':
                    state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
            elif self.env.context.get('from_finance_approve', False) or rec._context.get('button_finance_user', False):
                if rec.state != 'manager_approve':
                    state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
            elif self.env.context.get('from_return', False) or self.env.context.get('from_reject', False):
                if rec.state in ('new', 'reject', 'finance_approve'):
                    state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''

            if state:
                raise UserError(_('Vendor lead Creation is in %s state.Please Refresh' % (state)))
            form_view_id = self.env.ref('vendor_onboarding.vendor_lead_user_action_history_view_form').id
            ctx = self._context.copy()
            return {
                'name': _('Comments'),
                'view_type': 'form',
                'target': 'new',
                'context': ctx,
                "view_mode": 'form',
                'res_model': 'vendor.lead.user.action.history',
                'type': 'ir.actions.act_window',
                'view_id': form_view_id
            }

    def action_finance_approve(self):
        """perform to create new vendor.
        Function to change state from manager_approve to finance_approve"""
        for rec in self:
            doc_list = []
            if rec.document_ids:
                for doc in rec.document_ids:
                    new_dict = {
                        'document_name': doc.document_name,
                        'file': doc.file,
                        'file_name': doc.file_name,
                    }
                    doc_list.append((0, 0, new_dict))
            partner = self.env['res.partner'].with_context(default_supplier_rank=1).create({
                'name': rec.name,
                'supplier_rank': 1,
                'active': True,
                'street': rec.street,
                'street2': rec.street2,
                'city': rec.city,
                'state_id': rec.state_id.id,
                'zip': rec.zip,
                'country_id': rec.country_id.id,
                'vat': rec.vat,
                'region_id': rec.region_id.id,
                'phone': "+91" + rec.phone,
                'mobile': "+91" + rec.mobile if rec.mobile else False,
                'email': rec.email,
                'service_type_id': rec.service_type_id.id,
                'segment_id': rec.segment_id.id,
                'l10n_in_pan': rec.pan,
                'tax_tds_id': rec.tax_tds_id.id,
                'account_no': rec.account_no,
                'ifsc_code': rec.ifsc_code,
                'bank_name': rec.bank_name,
                'virtual_bank_acc': rec.virtual_bank_acc,
                'document_ids': doc_list,
            })
            if partner:
                partner.get_service_type_fleet()
                current_data = rec.approved_users or {}
                current_data.update({'finance_approved_user_id': self.env.user.id})
                rec.write({'partner_id': partner.id, 'state': 'finance_approve', 'approved_users': current_data})

    def _compute_is_editable(self):
        """
        Edit bool is used for giving edit access to specific fields for specific groups
        """
        for rec in self:
            rec.is_editable = True
            if rec.state == 'new':
                if self.env.user.has_group('vendor_onboarding.group_vendor_onboarding_create_access'):
                    rec.is_editable = True
                else:
                    rec.is_editable = False
            elif rec.state == 'pending_approval':
                if self.env.user.has_group('vendor_onboarding.group_vendor_onboarding_rm_approver'):
                    rec.is_editable = True
                else:
                    rec.is_editable = False
            elif rec.state == 'manager_approve':
                if self.env.user.has_group('vendor_onboarding.group_vendor_onboarding_finance_approver'):
                    rec.is_editable = True
                else:
                    rec.is_editable = False
            else:
                rec.is_editable = False

    def action_view_vendor(self):
        """to view the vendor through smart button in vendor onboarding view"""
        form_view = self.env.ref('base.view_partner_form')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'view_id': form_view.id,
            'context': {'create': False, 'default_supplier_rank': 1},
            'target': 'current',
        }

    def get_email_to(self):
        """ get email to"""
        joined_string = ""
        for record in self:
            group_obj = False
            emails = [self.env.user.partner_id.email or '']
            
            if record.create_uid.partner_id.email not in emails:
                if not self.env.context.get('from_return', False) or (self.env.context.get('from_return', False) and (
                        not record.approved_users or not record.approved_users.get('manager_approved_user_id', False))):
                    emails.append(record.create_uid.partner_id.email or '')
                    
            if self.env.context.get('from_send_for_approve', False):
                group_obj = self.env.ref('vendor_onboarding.group_vendor_onboarding_rm_approver')
                 
            elif self.env.context.get('from_manager_approve', False):
                group_obj = self.env.ref('vendor_onboarding.group_vendor_onboarding_finance_approver')
                
            elif self.env.context.get('from_return', False) or self.env.context.get('from_reject', False):
                if record.approved_users and record.approved_users.get('manager_approved_user_id', False):
                    approved_user = self.env['res.users'].browse(record.approved_users['manager_approved_user_id'])
                    if approved_user.partner_id.email not in emails:
                        emails.append(approved_user.partner_id.email or '')
                        
            if group_obj:
                for user in group_obj.users:
                    if user.partner_id.email not in emails:
                        emails.append(user.partner_id.email or '')
            if emails:
                joined_string = ",".join(emails)
        return joined_string

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    args.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    args.append(('region_id', 'in', []))
        res = super(VendorLead, self).search(args, offset, limit, order, count=count)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    domain.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    domain.append(('region_id', 'in', []))
        return super(VendorLead, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)
