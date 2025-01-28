import base64
import json
import re
from datetime import datetime
from operator import index

import requests
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import SUPERUSER_ID
from odoo.api import model, _logger
import ast


class CustomerOnboard(models.Model):
    _inherit = "customer.onboard"

    api_details_ids = fields.One2many(comodel_name='create.api.details', inverse_name='onboard_id')
    sync_status = fields.Selection(selection=[('failed', 'Failed'), ('success', 'Success')], string='Sync Status')
    v13_partner_id = fields.Integer(string='V13 Partner Id')

    def create_customer(self):
        res = super().create_customer()
        if res[0].id and res[1]:
            datas = res[1]
            self.create_customer_api(datas)
        return res

    def create_customer_api(self, datas):
        customer_data = self.prepare_customer_sync_data(datas)
        vals = {"params": customer_data}
        api_datails = self.env['create.api.details']

        api_credentials = self.env['qwqer.api.credentials'].sudo().search([], limit=1)
        if api_credentials and api_credentials.is_partner_update:

            headers = {
                'SecretKey': api_credentials.authorization,
                'content-type': "application/json",
            }
            url = api_credentials.server_url + '/api/create/customers'
            try:
                response = requests.request("POST", url, json=vals,
                                            headers=headers)
                response_data = response.json()['result']
                data = json.loads(response_data)
                if vals.get('params').get('documents'):
                    vals.get('params').pop("documents")
                if data['status_code'] == 200:
                    details = {
                        "api_name": "Customer Creation Api",
                        "data": vals,
                        "status": "success",
                        "response": data,
                        "onboard_id": self.id
                    }
                    self.sudo().update({'sync_status': 'success'})
                    self.sudo().update({'v13_partner_id': data['customer_id']})
                    if self.partner_id:
                        self.partner_id.customer_ref_key =  data['customer_id']
                        self.partner_id.wallet_id =  data['customer_id']
                        self.partner_id.is_wallet_active =  True

                else:
                    details = {
                        "api_name": "Customer Creation Api",
                        "data": vals,
                        "status": "failed",
                        "response": data,
                        "onboard_id": self.id
                    }
                    self.sudo().update({'sync_status': 'failed'})
                api_datails.sudo().create(details)

            except Exception as e:
                _logger.info("Error :exception happened : %s", e)
                details = {
                    "api_name": "Customer Creation Api",
                    "data": vals,
                    "status": "failed",
                    "response": e
                }
                api_datails.sudo().create(details)
            return True
        else:
            _logger.info("Credentials not added or not enabled the Customer Onboarding")

    def prepare_customer_sync_data(self, datas):
        segment = {
            'QWQER Fleet - FLeet FTL': 'QWQER Fleet - FTL',
            'QWQER Technologies - Fleet FTL': 'QWQER Fleet - FTL',
            'QWQER Technologies - UrbanHaul': 'QWQER Fleet - Urban Haul',
            'QWQER Fleet - Urban Haul': 'QWQER Fleet - Urban Haul',
            'QWQER Express - Large B2B': 'QWQER Express - Large B2B',
            'QWQER Express - Platform': 'QWQER Express - Platform',
            'QWQER Express - Rental': 'QWQER Express - Rental',
            'QWQER Express - SME': 'QWQER Express - SME',
            'QWQER Express - E-Comm': 'QWQER Express - E-Comm',
        }
        if datas:

            datas["product_line"] = self.product_line_id.name if self.product_line_id else False
            datas["credit_period_id"] = False
            datas["source_lead_type_id"] = self.source_id.name if self.source_id else False
            datas["followup_status_id"] = self.followup_status_id.name if self.followup_status_id else False
            datas["state_id"] = self.state_id.l10n_in_tin if self.state_id else False
            datas["country_id"] = self.country_id.code if self.country_id else False
            datas["region_id"] = self.region_id.region_code if self.region_id else False
            datas["order_sales_person"] = self.sales_person_id.work_email if self.sales_person_id else False
            datas["industry_id"] = self.industry_id.name if self.industry_id else False
            datas["potential_orders_id"] = self.potential_orders_id.name if self.potential_orders_id else False
            datas["delivery_type_id"] = self.delivery_type_id.name if self.delivery_type_id else False
            datas["invoice_frequency_id"] = self.invoice_frequency_id.name if self.invoice_frequency_id else False
            datas['payment_mode_ids'] = [mode.code for mode in self.payment_mode_ids] if self.payment_mode_ids else []
            datas['settlement_time_id'] = self.settlement_time_id.name if self.settlement_time_id else False
            datas['fleet_hsn_id'] = self.fleet_hsn_id.name if self.fleet_hsn_id else False
            datas['item_category_id'] = self.item_category_id.code if self.item_category_id else False
            datas['company_type'] = 'company'
            if self.customer_segment_id:
                segment_name = self.customer_segment_id.name
                if segment:
                    datas['segment_id'] = segment.get(segment_name)
            if self.contact_name:
                datas['contact_name'] = self.contact_name

            if self.customer_service_type_id.is_fleet_service:
                datas['service_type_id'] = 'vehicle_deployment'
                datas['vehicle_invoice_tax_ids'] = self.vehicle_invoice_tax_ids.mapped('name')
                return datas
            if self.customer_service_type_id.is_delivery_service:
                datas["service_type_id"] = "delivery"
                datas["b2b_invoice_tax_ids"] = self.b2b_invoice_tax_ids.mapped('name')
                datas["b2b_sale_order_tax_ids"] = self.b2b_sale_order_tax_ids.mapped('name')
            if self.customer_service_type_id.is_qshop_service:
                datas["service_type_id"] = "qwqershop"
                datas["qshop_invoice_tax_ids"] = self.qshop_invoice_tax_ids.mapped('name')
                datas["qshop_sale_order_tax_ids"] = self.qshop_sale_order_tax_ids.mapped('name')
            if self.pricing_model == 'KM' and self.km_pricing_plan_ids:
                km_plan_list = []
                for km_plan in self.km_pricing_plan_ids:
                    km_plan_data = {
                        "from_weight": km_plan.minimum_weight,
                        "to_weight": km_plan.maximum_weight,
                        "min_distance": km_plan.min_distance,
                        "min_cost": km_plan.min_cost,
                        "price": km_plan.price,
                    }
                    km_plan_list.append(km_plan_data)
                datas['pricing_plan'] = km_plan_list
                datas['pricing_model'] = 'KM'
            if self.pricing_model == 'slab' and self.slab_pricing_plan_ids:
                slab_plan_list = []
                for slab_plan in self.slab_pricing_plan_ids:
                    slab_plan_data = {
                        "minimum_weight": slab_plan.minimum_weight,
                        "maximum_weight": slab_plan.maximum_weight,
                        "from_distance": slab_plan.from_distance,
                        "to_distance": slab_plan.to_distance,
                        "price": slab_plan.price,
                    }
                    slab_plan_list.append(slab_plan_data)
                datas['pricing_plan'] = slab_plan_list
                datas['pricing_model'] = 'slab'
            if self.pricing_model == 'flat' and self.flat_pricing_plan_ids:
                flat_plan_list = []
                for flat_plan in self.flat_pricing_plan_ids:
                    flat_plan_data = {
                        "minimum_weight": flat_plan.minimum_weight,
                        "maximum_weight": flat_plan.maximum_weight,
                        "price": flat_plan.price,
                    }
                    flat_plan_list.append(flat_plan_data)
                datas['pricing_plan'] = flat_plan_list
                datas['pricing_model'] = 'flat'

            if self.additional_charges_ids:
                charge_plan_list = []
                for charges in self.additional_charges_ids:
                    charge_plan = {
                        "charge_type": charges.charge_type_id.name,
                        "amount_type": charges.amount_type,
                        "amount": charges.amount
                    }
                    charge_plan_list.append(charge_plan)
                datas["additional_charge"] = charge_plan_list
            doc_list = []
            if self.kyc_upload_document_ids:
                for rec in self.kyc_upload_document_ids:
                    vals = {
                        'document_name': rec.document_name,
                        'file_name': rec.file_name,
                        'file': base64.b64encode(rec.file).decode('utf-8') if rec.file else False
                    }
                    doc_list.append(vals)
            if self.pricing_plan_document_ids:
                for rec in self.kyc_upload_document_ids:
                    vals = {
                        'document_name': rec.document_name,
                        'file_name': rec.file_name,
                        'file': base64.b64encode(rec.file).decode('utf-8') if rec.file else False
                    }
                    doc_list.append(vals)
            if doc_list:
                datas['documents'] = doc_list

            return datas
