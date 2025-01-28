from email.policy import default

from odoo import api, models, fields, _
import re
from odoo.exceptions import ValidationError,UserError
from odoo import SUPERUSER_ID
from lxml import etree



class CrmLead(models.Model):
    _inherit = "crm.lead"

    customer_status = fields.Selection([('new_customer', 'New Merchant'),
                                      ('existing_customer', 'New Sub Merchant')],
                                       string="Customer Status", default='new_customer')
    brand_name = fields.Char()
    customer_type = fields.Selection([('b2c', 'B2C'), ('b2b', 'B2B')], string='Customer Type',default='b2b')
    customer_service_type = fields.Many2one('partner.service.type', "Service Type",
                                            domain="['|', ('company_id', '=', company_id), ('company_id', '=', False), ('is_customer', '=', True)]")
    phone_code = fields.Char(string="Code", default="+91")
    followup_status_id = fields.Many2one(
        'mail.activity.type', 'Follow-up Status',
        domain="[('res_model', '=', 'crm.lead'), ('company_id', '=', company_id) or ('company_id', '=', False)]",
        ondelete='restrict'
    )
    potential_monthly_revenue = fields.Float(string="Potential Monthly Revenue")
    region_id = fields.Many2one(comodel_name='sales.region', string='Region', domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    contact_name = fields.Char(string='Contact Name', required=1)
    customer_segment_id = fields.Many2one('partner.segment', string="Segment", domain="['|', ('company_id', '=', company_id), ('company_id', '=', False) , ('is_fleet_service', '!=', False)]")
    delivery_customer_segment_id = fields.Many2one('partner.segment', domain="['|', ('company_id', '=', company_id), ('company_id', '=', False) , ('is_fleet_service', '=', False),('is_customer','=',True)]")
    product_line_id = fields.Many2one("product.lines", string="Product Lines", tracking=True)
    delivery_type_id = fields.Many2one('delivery.type', string='Type of Delivery', copy=False, tracking=True)
    comments = fields.Text(string="Comments")
    pricing_model = fields.Selection([('KM', 'KM'),
                                      ('flat', 'FLAT'),
                                      ('slab', 'SLAB')], default='KM',
                                     string="Pricing Model")

    km_pricing_plan_ids = fields.One2many('pricing.plan', 'crm_lead_id', domain=[('select_plan_type', '=', 'KM')])
    flat_pricing_plan_ids = fields.One2many('pricing.plan', 'crm_lead_id', domain=[('select_plan_type', '=', 'flat')])
    slab_pricing_plan_ids = fields.One2many('pricing.plan', 'crm_lead_id', domain=[('select_plan_type', '=', 'slab')])
    is_crm_fleet_service = fields.Boolean(related='customer_service_type.is_fleet_service', store=True)
    is_crm_qshop_service = fields.Boolean(related='customer_service_type.is_qshop_service', store=True)
    customer_stop_count_ids = fields.One2many('customer.additional.charges','crm_id',string='Customer Stop Charges')
    attachment = fields.Binary(string='Attachment', attachment=True)
    file_name = fields.Char('File Name')
    existing_partner_id = fields.Many2one('res.partner', string="Parent Merchant",
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    merchant_phone_number = fields.Char("Merchant Phone Number")
    submerchant_billing = fields.Selection([('sub_merchant', 'Sub-Merchant'),
                                            ('main_merchant', 'Main-Merchant')],
                                           string="Sub-Merchant Billing", default='sub_merchant')
    phone = fields.Char(string="Phone", required=1, copy=False)
    is_mail_send = fields.Boolean(default=False)
    is_crm_lost = fields.Boolean(string="Is Lost", related='stage_id.is_lost', store=True)
    is_crm_won = fields.Boolean(string="Is Won", related='stage_id.is_won', store=True)
    is_crm_qualified = fields.Boolean(string="Is Qualified", related='stage_id.is_qualified', store=True)
    state_id = fields.Many2one('res.country.state')
    country_id = fields.Many2one('res.country',required=1,default=lambda self: self.env.company.country_id, string='Country')
    source_id = fields.Many2one('utm.source',string='Source/ Lead Type',required=True, ondelete='restrict')
    industry_id = fields.Many2one(comodel_name='res.partner.industry', string='Customer Industry')
    competition_id = fields.Many2many(comodel_name='competition.master', string='Competition')


    # @api.onchange('customer_service_type')
    # def onchange_customer_service_type(self):
    #     new_list = []
    #     self.customer_segment_id = False
    #     if self.customer_service_type.is_fleet_service:
    #         fleet_customer_segment_ids = self.env['partner.segment'].search(
    #             [('is_fleet_service', '=', True), ('is_customer', '=', True)])
    #         if fleet_customer_segment_ids:
    #             for segment_id in fleet_customer_segment_ids:
    #                 new_list.append(segment_id.id)
    #             return {'domain': {'customer_segment_id': [('id', 'in', new_list)]}}
    #     else:
    #         customer_segment_ids = self.env['partner.segment'].search(
    #             [('is_fleet_service', '=', False), ('is_customer', '=', True)])
    #         if customer_segment_ids:
    #             for segment_id in customer_segment_ids:
    #                 new_list.append(segment_id.id)
    #             return {'domain': {'customer_segment_id': [('id', 'in', new_list)]}}

    @api.onchange('region_id')
    def onchange_region_id(self):
        if self.region_id:
            for rec in self:
                rec.city = rec.region_id.name
                rec.state_id = rec.region_id.state_id.id


    # def action_send_quotation(self):
    #     """ CRM Send quotation : Open a wizard to compose an email, with relevant mail template loaded by default """
    #     template_id = self.env.ref('crm_lead_management.crm_send_quotation_mail_template')
    #     if template_id:
    #         if self.id:
    #             template_id.send_mail(self.id, email_values=None, force_send=True)
    #             self.write({'is_mail_send': True})

    @api.onchange('phone')
    def onchange_phone_validation(self):
        for rec in self:
            if rec.phone:
                # Checking Number is valid or not and it contains 10 digits or not
                if re.match(r'^[0-9]+$', rec.phone) is None or len(rec.phone) != 10:
                    rec.phone = False
                    return {
                        'warning': {
                            'title': "Invalid Value",
                            'message': "Enter valid 10 digits Mobile number",
                        }
                    }
                crm_phone_exist = self.env['crm.lead'].search([('phone', '=', rec.phone)])
                partner_phone_exist = self.env['res.partner'].search(['|',('phone', 'like',rec.phone),('mobile','like',rec.phone)])
                if crm_phone_exist:
                    phone = rec.phone
                    rec.phone = False
                    return {
                        'warning': {
                            'title': "Invalid Value",
                            'message': ('Crm Lead Already Exists for this Phone Number  %s . This is Created by  %s  and Created on  %s . So, You Cannot Create New Crm Lead with this Phone Number.') % (
                            phone, crm_phone_exist.create_uid.name, crm_phone_exist.create_date.date())
                        }
                    }
                if partner_phone_exist:
                    phone = rec.phone
                    rec.phone = False
                    return {
                        'warning': {
                            'title': "Invalid Value",
                            'message': ('Partner Already Exists for this Phone Number  %s . This is Created by  %s  and Created on  %s . So, You Cannot Create New Crm Lead with this Phone Number.') % (
                            phone, partner_phone_exist.create_uid.name, partner_phone_exist.create_date.date())
                        }
                    }

    @api.constrains('phone')
    def phone_validation(self):
        for rec in self:
            if rec.phone:
                # Checking Number is valid or not and it contains 10 digits or not
                if re.match(r'^[0-9]+$', rec.phone) is  None or len(rec.phone) != 10:
                        raise ValidationError("Enter valid 10 digits Mobile number")
                crm_phone_exist = self.env['crm.lead'].search([('phone', '=', rec.phone), ('id', '!=', rec.id)])
                if crm_phone_exist:
                    raise ValidationError(
                            _('Crm Lead Already Exists for this Phone Number  %s . This is Created by  %s  and Created on  %s . So, You Cannot Create New Crm Lead with this Phone Number.') % (
                            rec.phone, crm_phone_exist.create_uid.name, crm_phone_exist.create_date.date()))

    # Filter leads based on the user associated regions

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    args.append(('region_id', 'in', [False]+self.env.user.displayed_regions_ids.ids))
                else:
                    args.append(('region_id', 'in', []))
        res = super(CrmLead, self).search(args, offset, limit, order, count=count)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    domain.append(('region_id', 'in', [False]+self.env.user.displayed_regions_ids.ids))
                else:
                    domain.append(('region_id', 'in', []))
        return super(CrmLead, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)

    @api.onchange('customer_service_type')
    def onchange_service_type(self):
        if self.customer_service_type.is_fleet_service:
            self.customer_type = 'b2b'

    def action_set_lost(self, **additional_values):
        """ Lost semantic: probability = 0 or active = True """
        stage_id = self._stage_find(domain=[('is_lost', '=', True)])
        result = self.write({'active': True, 'probability': 0, 'automated_probability': 0, **additional_values, 'stage_id': stage_id.id})
        return result

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        stages = {
            'qualified': self.env.ref('crm.stage_lead2'),
            'won': self.env.ref('crm.stage_lead4'),
            'new': self.env.ref('crm.stage_lead1'),
            'lost': self.env.ref('crm_lead_management.stage_lead5'),
        }
        for rec in self:
            if rec._origin.stage_id.id in [stages['new'].id] and rec.stage_id.id in [stages['lost'].id]:
                raise UserError("You are not allowed to perform this operation from here. Click the 'Lost' button to change the lead to the 'Lost' state.")
            if rec._origin.stage_id.id in [stages['new'].id] and rec.stage_id.id in [stages['won'].id]:
                raise UserError("You can't move a lead directly from the New stage to the Won stage. You must first Qualify the lead.")
            if rec._origin.stage_id.id in [stages['qualified'].id] and rec.stage_id.id in [stages['lost'].id]:
                raise UserError("You are not allowed to perform this operation from here. Click the 'Lost' button to change the lead to the 'Lost' state.")
            if rec._origin.stage_id.id in [stages['qualified'].id] and rec.stage_id.id in [stages['new'].id]:
                raise UserError("You can't move a lead from the Qualified stage to the New stage.")
            if rec._origin.stage_id.id in [stages['won'].id] and rec.stage_id.id in [stages['new'].id]:
                raise UserError("You can't move a lead from the Won stage to the New stage.")
            if rec._origin.stage_id.id in [stages['won'].id] and rec.stage_id.id in [stages['lost'].id] and not self.env.user.has_group('crm_lead_management.crm_lead_stage_move_group'):
                raise UserError("You can't move a lead from the Won stage to the Lost stage.")
            if rec._origin.stage_id.id in [stages['won'].id] and rec.stage_id.id in [stages['qualified'].id]:
                raise UserError("You can't move a lead from the Won stage to the Qualified stage.")
            if rec._origin.stage_id.id in [stages['lost'].id] and rec.stage_id.id in [stages['qualified'].id]:
                raise UserError("You can't move a lead from the Lost stage to the Qualified stage.")
            if rec._origin.stage_id.id in [stages['lost'].id] and rec.stage_id.id in [stages['won'].id]:
                raise UserError("You can't move a lead from the Lost stage to the Won stage.")
            if rec._origin.stage_id.id in [stages['lost'].id] and rec.stage_id.id in [stages['new'].id] and not self.env.user.has_group('crm_lead_management.crm_lead_stage_move_group'):
                raise UserError("You can't move a lead from the Lost stage to the New stage.")


            if rec._origin.stage_id:
                required_field_list = []
                if rec.is_crm_fleet_service:
                    customer_segment = "customer_segment_id"
                else:
                    customer_segment = "delivery_customer_segment_id"
                for field_name, field_obj in rec._fields.items():
                    if field_obj.required or field_name in ["name", "phone", "customer_service_type", "source_id", "followup_status_id", "region_id", "contact_name",customer_segment, "state_id","date_deadline","competition_id"]:
                        field_value = getattr(rec, field_name)

                        # To Handle Many2one fields
                        if isinstance(field_value, models.BaseModel):
                            # if len(field_value)>1 and field_value
                            if not field_value.ids:
                                required_field_list.append(field_obj.string)
                        else:
                            # For other fields
                            if not field_value:
                                required_field_list.append(field_obj.string)
                if required_field_list:
                    field_str = ", ".join(required_field_list)
                    raise ValidationError(_("The following required field(s) are empty: %s." % field_str))

    def write(self, vals):
        for rec in self:
            if rec.stage_id == self.env.ref('crm.stage_lead4') and not vals.get("customer_onboard_id"):
                raise ValidationError(_(
                    f"You are not allowed to make any changes after won"
                ))
        res = super().write(vals)
        for rec in self:
            if (rec.street and len(rec.street) > 100) or (rec.street2 and len(rec.street2) > 100):
                raise UserError(_("Address line should not exceed 100 words"))

        return res


    @api.onchange('existing_partner_id')
    def _onchange_parent_partner_id(self):
        for rec in self:
            if rec.existing_partner_id and rec.existing_partner_id.phone:
                rec.merchant_phone_number = rec.existing_partner_id.phone