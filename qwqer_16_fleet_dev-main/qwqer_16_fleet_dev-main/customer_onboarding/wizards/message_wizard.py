# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MessageWizard(models.TransientModel):
    _name = 'message.wizard'

    message = fields.Text(string='Message', required=True)
    is_warning = fields.Boolean(string="Is Warning?")

    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}

    def action_update(self):
        if self._context.get('active_model') == 'customer.onboard' and self._context.get('active_id', False):
            customer_ob_rec = self.env['customer.onboard'].browse([self._context.get('active_id', False)])
            phone = ""
            if customer_ob_rec.phone:
                phone = customer_ob_rec.phone_code + customer_ob_rec.phone
            existing_partner = self.env['res.partner'].search([('phone', '=', phone)])
            if existing_partner:
                existing_partner.write({
                    'name': customer_ob_rec.customer_name,
                    'is_company': True,
                    'customer_rank': 1,
                    'email': customer_ob_rec.customer_email,
                    'street': customer_ob_rec.street,
                    'street2': customer_ob_rec.street2,
                    'city': customer_ob_rec.city,
                    'zip': customer_ob_rec.zip,
                    'country_id': customer_ob_rec.id,
                    'active': True,
                    'vat': customer_ob_rec.gstin_number,
                    'l10n_in_pan': customer_ob_rec.tax_id,
                    'customer_type': customer_ob_rec.customer_type,
                    'phone': phone,
                    # 'b2b_invoice_tax_ids': self.b2b_invoice_tax_ids.ids,
                    # 'b2b_sale_order_tax_ids': self.b2b_sale_order_tax_ids.ids,
                    'vehicle_invoice_tax_ids': customer_ob_rec.vehicle_invoice_tax_ids or False,
                    'fleet_hsn_id': customer_ob_rec.fleet_hsn_id.id or False,
                    'vehicle_invoice_frequency': customer_ob_rec.vehicle_invoice_frequency or False,
                    'region_id': customer_ob_rec.region_id.id,
                    'order_sales_person': customer_ob_rec.sales_person_id.id,
                    # 'invoice_frequency_id': self.invoice_frequency_id.id,
                    'source_lead_type_id': customer_ob_rec.source_id.id,
                    'industry_id': customer_ob_rec.industry_id.id,
                    'followup_status_id': customer_ob_rec.followup_status_id.id,
                    'pricing_type': customer_ob_rec.pricing_type,
                    # 'pricing_model': self.pricing_model,
                    'payment_mode_ids': customer_ob_rec.payment_mode_ids.ids,
                    'potential_orders_id': customer_ob_rec.potential_orders_id.id or False,
                    # 'is_fifo_flow': self.is_fifo_flow or False,
                    # 'max_no_de': self.max_no_de or False,
                    'delivery_type_id': customer_ob_rec.delivery_type_id or False,
                    'pick_up_area': customer_ob_rec.pick_up_area or False,
                    'distance_limitation': customer_ob_rec.distance_limitation or False,
                    'api_selection': customer_ob_rec.api_selection or False,
                    'product_storage': customer_ob_rec.product_storage or False,
                    'product_sorting': customer_ob_rec.product_sorting or False,
                    'item_category_id': customer_ob_rec.item_category_id.id or False,
                    'sms_alert': customer_ob_rec.sms_alert or False,
                    'email_alert': customer_ob_rec.email_alert or False,
                    'service_type_id': customer_ob_rec.customer_service_type_id.id or False,
                    'segment_id': customer_ob_rec.customer_segment_id.id or False,
                    'product_line_id': customer_ob_rec.product_line_id.id or False,
                })
            if existing_partner.child_ids:
                for child in existing_partner.child_ids:
                    if child.name == customer_ob_rec.contact_name:
                        customer_ob_rec.contact_partner_id = child.id
            if customer_ob_rec.contact_partner_id:
                customer_ob_rec.contact_partner_id.name = customer_ob_rec.contact_name
            else:
                # create contact for created partner
                contact_partner = self.env['res.partner'].create({'name': customer_ob_rec.contact_name,
                                                                  'type': 'contact',
                                                                  'email': customer_ob_rec.customer_email,
                                                                  'street': customer_ob_rec.street,
                                                                  'street2': customer_ob_rec.street2,
                                                                  'city': customer_ob_rec.city,
                                                                  'state_id': customer_ob_rec.state_id.id,
                                                                  'zip': customer_ob_rec.zip,
                                                                  'country_id': customer_ob_rec.country_id.id,
                                                                  'parent_id': existing_partner.id,
                                                                  'active': True,
                                                                  'customer_type': customer_ob_rec.customer_type,
                                                                  'sms_alert': customer_ob_rec.sms_alert or False,
                                                                  'email_alert': customer_ob_rec.email_alert or False,
                                                                  'segment_id': customer_ob_rec.customer_segment_id.id or False,
                                                                  })
                customer_ob_rec.contact_partner_id = contact_partner.id
            customer_ob_rec.partner_id = existing_partner.id
            if customer_ob_rec.is_fleet_service_customer:
                state_from = 'finance_approvals'
                state_to = 'configurations_completed'
            else:
                state_from = 'under_pricing_config'
                state_to = 'configurations_completed'
            customer_ob_rec.create_user_history(state_from, state_to)
            customer_ob_rec.state = 'configurations_completed'
            return True
