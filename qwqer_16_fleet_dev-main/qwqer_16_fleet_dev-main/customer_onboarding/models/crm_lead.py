from odoo import api, models, fields, _
import re
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = "crm.lead"

    customer_onboard_id = fields.Many2one(comodel_name='customer.onboard', string="Onboarded Customer",readonly=1)

    def action_customer_onboard(self):

        customer_ob_phone_exist = self.env['customer.onboard'].search([('phone', '=', self.phone)])
        if customer_ob_phone_exist:
            for customer_ob_phone_exist in customer_ob_phone_exist:
                raise ValidationError(
                    _('Customer Onboarding Already Exists for this Phone Number  %s . This is Created by  %s  and Created on  %s . So, You Cannot Create New Customer with this Phone Number.') % (
                        self.phone, customer_ob_phone_exist.create_uid.name, customer_ob_phone_exist.create_date))
        if self.user_id:
            employee_id = self.env['hr.employee'].search([('user_id','=',self.user_id.id),('company_id','=',self.env.company.id)])
            if not employee_id:
                raise ValidationError(_('No employee found for this user.'))
            else:
                dict_vals = {
                    'customer_name': self.name or False,
                    'brand_name': self.brand_name or False,
                    'phone': self.phone or False,
                    'contact_name': self.contact_name or False,
                    'customer_service_type_id': self.customer_service_type.id or False,
                    'customer_segment_id': self.customer_segment_id.id or self.delivery_customer_segment_id.id,
                    'source_id': self.source_id.id or False,
                    'customer_type': self.customer_type or False,
                    'delivery_type_id': self.delivery_type_id.id or False,
                    'followup_status_id': self.followup_status_id.id or False,
                    'region_id': self.region_id.id or False,
                    'pick_up_area':self.region_id.name or False,
                    'product_line_id': self.product_line_id.id or False,
                    'street': self.street or False,
                    'street2': self.street2 or False,
                    'city': self.city or False,
                    'state_id': self.state_id.id or False,
                    'zip': self.zip or False,
                    'country_id': self.country_id.id or False,
                    'customer_email': self.email_from or False,
                    'expected_revenue':self.potential_monthly_revenue or False,
                    'date_deadline':self.date_deadline or False,
                    'customer_status' : self.customer_status or False,
                    'parent_partner_id' : self.existing_partner_id.id or False,
                    'merchant_phone_number' : self.merchant_phone_number or False,
                    'submerchant_billing':self.submerchant_billing or False,
                    'pricing_model':self.pricing_model or False,
                    'industry_id':self.industry_id.id or False,

                }
                customer_onboard_id = self.env['customer.onboard'].sudo().create(dict_vals)
                if customer_onboard_id:
                    customer_onboard_id.get_service_type()
                    customer_onboard_id.get_corresponding_user()
                    self.customer_onboard_id = customer_onboard_id.id
                    if self.km_pricing_plan_ids:
                        for rec in self.km_pricing_plan_ids:
                            rec.customer_ob_plan_id = customer_onboard_id.id
                    if self.slab_pricing_plan_ids:
                        for rec in self.slab_pricing_plan_ids:
                            rec.customer_ob_plan_id = customer_onboard_id.id
                    if self.flat_pricing_plan_ids:
                        for rec in self.flat_pricing_plan_ids:
                            rec.customer_ob_plan_id = customer_onboard_id.id
                    if self.customer_stop_count_ids:
                        for rec in self.customer_stop_count_ids:
                            rec.customer_onboard_id = customer_onboard_id.id

    def action_view_onboard_customer(self):
        """to view the onboarded  through smart button in crm lead view view"""
        form_view = self.env.ref('customer_onboarding.customer_onboard_form_view')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'customer.onboard',
            'res_id': self.customer_onboard_id.id,
            'view_mode': 'form',
            'view_id': form_view.id,
            'context': {'create': False, 'default_customer_rank': 1},
            'target': 'current',
        }
