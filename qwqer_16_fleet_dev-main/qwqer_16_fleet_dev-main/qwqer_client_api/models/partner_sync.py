# -*- coding: utf-8 -*-
import base64
from email.policy import default

import requests
from PIL.ImageChops import offset

from odoo import fields, models, api, _
from odoo.api import model, _logger
from odoo.exceptions import ValidationError, UserError
import json
import markdown
from bs4 import BeautifulSoup



class PartnerSyncApi(models.Model):
    _name = 'partner.sync.api'
    _description = 'model for fetching partner details from v13 and creating new customer in v16'
    _order = 'id desc'


    partner_service_type = fields.Selection(selection=[('delivery', 'Delivery'), ('qwqershop', 'Qshop'),('vehicle_deployment','Fleet Service')],
                                            string='Partner Service Type')
    state = fields.Selection(
        selection=[('new', 'New'), ('pending', 'Pending'), ('incomplete', 'Completed With Failure'),
                   ('completed', 'Completed')], default='new')
    partner_type = fields.Selection(selection=[('customer', 'Customer'), ('vendor', 'Vendor')])
    fetch_limit = fields.Integer('Limit',)
    offset_no = fields.Integer(string='Offset', store=True)
    api_details_ids = fields.One2many(comodel_name='create.api.details', inverse_name='customer_sync_id')
    b_type =  fields.Selection(selection=[('b2b', 'B2B'), ('b2c', 'B2C')],
                                            string='Type')
    partner_id= fields.Integer(string="Id")



    def get_customer_data(self):
        self.get_offset_value()
        api_credentials = self.env['qwqer.api.credentials'].sudo().search([], limit=1)
        if api_credentials and api_credentials.is_partner_sync:
            for rec in self:
                url = api_credentials.server_url +'/api/customers'
                params = {
                    'service_type': rec.partner_service_type,
                    'partner_type': rec.partner_type,
                    'limit': rec.fetch_limit,
                    'offset': rec.offset_no,
                    'b_type': rec.b_type,
                    'partner_id':rec.partner_id
                }
                try:
                    response = requests.get(url, params=params)
                    if response.status_code == 200:
                        # Convert the response from JSON format
                        data = response.json()
                        if data:
                            self.create_customer(data['data'])
                except Exception as e:
                    _logger.info("Error :exception happened : %s", e)
                    raise UserError(e)

        else:
            _logger.info("Credentials not added or not enabled the Customer Syncing")

    def get_offset_value(self):
        for rec in self:
            if not rec.partner_id:
                if rec.partner_service_type and rec.partner_type:
                    if rec.fetch_limit > 0:
                        last_record = self.env['partner.sync.api'].search(
                            [('partner_service_type', '=', rec.partner_service_type),
                             ('partner_type', '=', rec.partner_type),('b_type','=',rec.b_type) ,('id', '!=', rec.id)],
                            order='create_date desc',
                            limit=1
                        )
                        if last_record:
                            rec.offset_no = last_record.offset_no + last_record.fetch_limit
                        else:
                            rec.offset_no = False
                    else:
                        raise ValidationError('Limit Should greater than Zero')


    def create_customer(self, data):
        for rec in data:
            try:
                if rec.get('customer_id'):
                    customer_ref_key = rec.get('customer_id')
                    existing_partner_id = self.env['res.partner'].search([('customer_ref_key', '=', customer_ref_key),('company_id', '=', self.env.company.id)])
                    if not existing_partner_id:
                        order_sales_person = False
                        order_placement = False
                        potential_orders = False
                        delivery_type = False
                        item_categ = False
                        follow_up = False
                        source_id = False
                        industry_id = False
                        settlement_time = False
                        product_line_id = False
                        invoice_frequency_id = False
                        fleet_hsn_id = False
                        state = self.env['res.country.state'].search(
                            [('code', '=', rec['address']['state']),
                             ('country_id', '=', rec.get('address').get('country'))],limit=1)
                        country = self.env['res.country'].search([('code', '=', rec.get('address').get('country'))],limit=1)
                        region = self.env['sales.region'].search(
                            [('region_code', '=', rec.get('region_id')), ('company_id', '=', self.env.company.id)],limit=1)
                        segment = self.env['partner.segment'].search([('name', '=', rec.get('segment_id'))],limit=1)
                        if rec.get('order_sales_person'):
                            sale_person_mail = rec.get('order_sales_person')
                            if sale_person_mail:
                                order_sales_person = self.env['hr.employee'].search(
                                    [('work_email', '=', sale_person_mail), ('company_id', '=', self.env.company.id)],limit=1)
                        if rec.get('source_type_id'):
                            order_placement = self.env['source.type'].search([('name', '=', rec['source_type_id'])],limit=1)
                        if rec.get('potential_orders_id'):
                            potential_orders = self.env['potential.orders'].search(
                                [('name', '=', rec['potential_orders_id'])],limit=1)
                        if rec.get('industry_id'):
                            industry_id = self.env['res.partner.industry'].search(
                                [('name', '=', rec['industry_id'])],limit=1)
                        if rec.get('settlement_time_id'):
                            settlement_time = self.env['settlement.time'].search(
                                [('name', '=', rec['settlement_time_id'])],limit=1)
                        if rec.get('delivery_type_ids'):
                            delivery_type = self.env['delivery.type'].search([('name', '=', rec['delivery_type_ids'])],limit=1)
                        if rec.get('item_category_id'):
                            item_categ = self.env['item.category'].search([('code', '=', rec['item_category_id'])],limit=1)
                        if rec.get('followup_status_id'):
                            follow_up = self.env['mail.activity.type'].search(
                                [('name', '=', rec['followup_status_id']), ('company_id', '=', self.env.company.id)],limit=1)
                        if rec.get('source_lead_type_id'):
                            source_id = self.env['utm.source'].search([('name', '=', rec.get('source_lead_type_id'))],limit=1)
                        if rec.get('product_line'):
                            product_line_id = self.env['product.lines'].search([('name','=',rec.get('product_line'))],limit=1)
                        if rec.get('invoice_frequency_id'):
                            invoice_frequency_id = self.env['invoice.frequency'].search([('name', '=', rec.get('invoice_frequency_id'))],limit=1)
                        if rec.get('fleet_hsn_id'):
                            fleet_hsn_id = self.env['product.template'].search(
                                [('name', '=', rec.get('fleet_hsn_id'))], limit=1)
                        if self.partner_service_type == 'delivery':
                            service_type = self.env['partner.service.type'].search([('is_delivery_service', '=', True)],limit=1)
                        elif self.partner_service_type == 'qwqershop':
                            service_type = self.env['partner.service.type'].search([('is_qshop_service', '=', True)],limit=1)
                        elif self.partner_service_type == 'vehicle_deployment':
                            service_type = self.env['partner.service.type'].search([('is_fleet_service','=',True)],limit=1)
                        else:
                            service_type = False

                        vals = {
                            "customer_ref_key": rec.get('customer_id') or False,
                            'company_type':rec.get('company_type') or False,
                            "name": rec.get('name'),
                            "street": rec.get('address').get('street') or False,
                            "street2": rec.get('address').get('street2'),
                            "city": rec.get('address').get('city'),
                            "state_id": state.id if state else False,
                            "zip": rec.get('address').get('zip'),
                            "country_id": country.id if country else False,
                            "customer_type": rec.get('customer_type'),
                            "email": rec.get('email'),
                            "phone": rec.get('phone'),
                            "is_fifo_flow": rec.get('is_fifo_flow') or False,
                            "max_no_de": rec.get('max_no_de') or False,
                            "region_id": region.id if region else False,
                            "service_type_id": service_type and service_type.id or False,
                            "segment_id": segment.id,
                            "vat": rec.get('vat') or False,
                            "state_region_id": region.state_id.id if region else False,
                            "virtual_bank_acc": rec.get('virtual_bank_acc'),
                            "wallet_id": rec.get('wallet_id'),
                            "is_wallet_active": rec.get('is_wallet_active'),
                            "l10n_in_pan": rec.get('tax_id'),
                            "mobile": rec.get('mobile'),
                            "order_sales_person": order_sales_person.id if order_sales_person else False,
                            "tds_threshold_check": rec.get('tds_threshold_check'),
                            "account_no": rec.get('account_no'),
                            "ifsc_code": rec.get('ifsc_code'),
                            "beneficiary": rec.get('beneficiary'),
                            "bank_name": rec.get('bank_name'),
                            "source_lead_type_id": source_id.id if source_id else False,
                            "industry_id": industry_id.id if industry_id else False,
                            "source_type_id": order_placement.id if order_placement else False,
                            "potential_orders_id": potential_orders.id if potential_orders else False,
                            "delivery_type_id": delivery_type.id if delivery_type else False,
                            "pick_up_area": rec.get('pick_up_area'),
                            "item_category_id": item_categ.id if item_categ else False,
                            "product_line_id": product_line_id.id if product_line_id else False,
                            "invoice_frequency_id": invoice_frequency_id.id if invoice_frequency_id else False,
                            "followup_status_id": follow_up.id if follow_up else False,
                            "pricing_type": rec.get('pricing_type'),
                            "distance_limitation": rec.get('distance_limitation'),
                            "sms_alert": rec.get('sms_alert'),
                            "email_alert": rec.get('email_alert'),
                            "api_selection": rec.get('api_selection'),
                            "product_storage": rec.get('product_storage'),
                            "product_sorting": rec.get('product_sorting'),
                            "customer_rank": rec.get('customer_rank'),
                            "supplier_rank": rec.get('supplier_rank'),
                            "pricing_model": rec.get('pricing_model'),
                            "merchant_amount_collection": rec.get('merchant_amount_collection'),
                            "amount_collection_limit": rec.get('amount_collection_limit'),
                            "collection_charges": rec.get('collection_charges'),
                            "settlement_time_id": settlement_time.id if settlement_time else False,
                            "fleet_hsn_id": fleet_hsn_id.id if fleet_hsn_id else False

                        }
                        if self.partner_service_type == 'delivery':
                            inv_tax_list = []
                            sale_tax_list = []
                            for inv_tax in rec.get('b2b_invoice_tax_ids'):
                                inv_tax_id = self.env['account.tax'].search(
                                    [('name', '=', inv_tax), ('company_id', '=', self.env.company.id)],limit=1)
                                if inv_tax_id:
                                    inv_tax_list.append(inv_tax_id.id)
                            for sale_tax in rec.get('b2b_sale_order_tax_ids'):
                                sale_tax_id = self.env['account.tax'].search(
                                    [('name', '=', sale_tax), ('company_id', '=', self.env.company.id)],limit=1)
                                if sale_tax_id:
                                    sale_tax_list.append(sale_tax_id.id)
                            vals.update({
                                'b2b_invoice_tax_ids': [
                                    (6, 0, inv_tax_list)] if inv_tax_list else None,
                                'b2b_sale_order_tax_ids': [
                                    (6, 0, sale_tax_list)] if sale_tax_list else None,
                                'is_delivery_customer': True
                            })

                        if self.partner_service_type == 'qwqershop':
                            qshop_inv_tax_list = []
                            qshop_sale_tax_list = []
                            for inv_tax in rec.get('qshop_invoice_tax_ids'):
                                inv_tax_id = self.env['account.tax'].search(
                                    [('name', '=', inv_tax), ('company_id', '=', self.env.company.id)],limit=1)
                                if inv_tax_id:
                                    qshop_inv_tax_list.append(inv_tax_id.id)
                            for sale_tax in rec.get('qshop_sale_order_tax_ids'):
                                sale_tax_id = self.env['account.tax'].search(
                                    [('name', '=', sale_tax), ('company_id', '=', self.env.company.id)],limit=1)
                                if sale_tax_id:
                                    qshop_sale_tax_list.append(sale_tax_id.id)
                            vals.update({
                                'qshop_invoice_tax_ids': [
                                    (6, 0, qshop_inv_tax_list)] if qshop_inv_tax_list else False,
                                'qshop_sale_order_tax_ids': [
                                    (6, 0, qshop_sale_tax_list)] if qshop_sale_tax_list else False,
                                'is_qshop_customer': True
                            })
                        if self.partner_service_type == 'vehicle_deployment':
                            fleet_tax_list = []
                            for fleet_tax in rec.get('vehicle_invoice_tax_ids'):
                                fleet_tax_id = self.env['account.tax'].search(
                                    [('name', '=', fleet_tax), ('company_id', '=', self.env.company.id)],limit=1)
                                if fleet_tax_id:
                                    fleet_tax_list.append(fleet_tax_id.id)
                            vals.update({
                                'vehicle_invoice_tax_ids': [
                                    (6, 0, fleet_tax_list)] if fleet_tax_list else False,
                                'is_fleet_partner': True
                            })
                        if rec.get('payment_mode_ids'):
                            payment_list = []
                            for mode in rec['payment_mode_ids']:
                                mode = self.env['payment.mode'].search([('code', '=', mode)])
                                payment_list.append(mode.id)
                            vals.update({
                                'payment_mode_ids': [(6, 0, payment_list)]})
                        if rec.get('pricing_plan_data') and rec.get('pricing_model'):
                            if rec.get('pricing_model') == 'KM':
                                plan = []
                                for km_plan in rec.get('pricing_plan_data'):
                                    val = {
                                        'minimum_weight': km_plan['from_weight'],
                                        'maximum_weight': km_plan['to_weight'],
                                        'min_distance': km_plan['min_distance'],
                                        'min_cost': km_plan['min_cost'],
                                        'per_km_charge': km_plan['per_km_charge'],
                                        'select_plan_type': 'KM'
                                    }
                                    plan.append((0, 0, val))
                                vals.update({'km_pricing_plan_ids': plan})

                            if rec.get('pricing_model') == 'slab':
                                plan = []
                                for slab_plan in rec['pricing_plan_data']:
                                    val = {
                                        'minimum_weight': slab_plan['from_weight'],
                                        'maximum_weight': slab_plan['to_weight'],
                                        'from_distance': slab_plan['from_distance'],
                                        'to_distance': slab_plan['to_distance'],
                                        'price': slab_plan['price'],
                                        'select_plan_type': 'slab'
                                    }
                                    plan.append((0, 0, val))
                                vals.update({'slab_pricing_plan_ids': plan})

                            if rec.get('pricing_model') == 'flat':
                                plan = []
                                for flat_plan in rec['pricing_plan_data']:
                                    val = {
                                        'minimum_weight': flat_plan['from_weight'],
                                        'maximum_weight': flat_plan['to_weight'],
                                        'price': flat_plan['price'],
                                        'select_plan_type': 'flat'
                                    }
                                    plan.append((0, 0, val))
                                vals.update({'flat_pricing_plan_ids': plan})
                        if rec.get('additional_charge'):
                            charge_list = []
                            for charges in rec['additional_charge']['additional_charge']:
                                charge_id = self.env['charge.type'].search([('name', '=', charges['charge_type_id'])],limit=1)
                                charges['charge_type_id'] = charge_id.id
                                charge_list.append((0, 0, charges))
                            vals.update({'additional_charges_ids': charge_list})
                        if rec.get('document_ids'):
                            try:
                                doc_list = []
                                for doc in rec['document_ids']:
                                    doc = {
                                        'document_name': doc.get('document_name'),
                                        'file_name': doc.get('file_name'),
                                        'file': base64.b64decode(doc.get('file')) if doc.get('file') else False
                                    }
                                    doc_list.append((0, 0, doc))
                                vals.update({'document_ids': doc_list})
                            except Exception as e:
                                if rec.get('document_ids'):
                                    rec.pop("document_ids")
                                _logger.info("Error :exception happened : %s", e)
                                self.env['create.api.details'].create({
                                    'api_name': 'Customer Sync Api',
                                    'customer_sync_id': self.id,
                                    'status': 'failed',
                                    'data': vals,
                                    'response': e,
                                })


                        try:
                            partner = self.env['res.partner'].create(vals)
                            _logger.info("customer created : %s", partner.id)

                            if partner:
                                if vals.get('document_ids'):
                                    vals.pop("document_ids")
                                self.env['create.api.details'].create({
                                    'api_name': 'Customer Sync Api',
                                    'customer_sync_id': self.id,
                                    'status': 'success',
                                    'data': vals,
                                    'response': "Customer Created",
                                    'partner_id': partner.id,

                                })
                                if rec.get('contact'):

                                    for contact in rec.get('contact'):
                                        contact_vals = {
                                            'name': contact.get('name'),
                                            'type': 'contact',
                                            'email': contact.get('email'),
                                            'street': contact.get('street'),
                                            'street2': contact.get('street2'),
                                            'city': contact.get('city'),
                                            'state_id': state.id,
                                            'zip': contact.get('zip'),
                                            'country_id': country.id,
                                            'parent_id': partner.id,
                                            'active': True,
                                            'customer_type': contact.get('customer_type'),
                                        }
                                    contact_partner = self.env['res.partner'].create(contact_vals)
                        except Exception as e:
                            if vals.get('document_ids'):
                                vals.pop("document_ids")
                            _logger.info("Error :exception happened : %s", e)
                            self.env['create.api.details'].create({
                                'api_name': 'Customer Sync Api',
                                'customer_sync_id': self.id,
                                'status': 'failed',
                                'data': vals,
                                'response': e,
                            })
                    else:
                        if rec.get('document_ids'):
                            rec.pop("document_ids")
                        self.env['create.api.details'].create({
                            'api_name': 'Customer Sync Api',
                            'customer_sync_id': self.id,
                            'status': 'failed',
                            'data': rec,
                            'response': "Already a customer  with this {cus_phone} Customer Reference Id : customer name is {customer}".format(
                                cus_phone=customer_ref_key, customer=existing_partner_id),
                        })


                else:
                    if rec.get('document_ids'):
                        rec.pop("document_ids")
                    self.env['create.api.details'].create({
                        'api_name': 'Customer Sync Api',
                        'customer_sync_id': self.id,
                        'status': 'failed',
                        'data': rec,
                        'response': "Customer Id is Missing"
                    })
                self.env.cr.commit()
            except Exception as e:
                try:
                    self.env.cr.rollback()
                except:
                    pass
                self.env['create.api.details'].create({
                    'api_name': 'Customer Sync Api',
                    'customer_sync_id': self.id,
                    'status': 'failed',
                    'data': rec,
                    'response': f"Exception occurred {str(e)}"
                })
        if self.api_details_ids:
            failed_rec = self.api_details_ids.filtered(lambda s: s.status == 'failed')
            if failed_rec:
                self.state = 'incomplete'
            else:
                self.state = 'completed'


class ResPatherUpdateSync(models.Model):
    _inherit = 'res.partner'


    def update_success_notify(self, message):
        res = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': message,
                'sticky': False,
                'type': 'success',
            }
        }
        return res

    def updatet_failed_notify(self, message):
        res = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Failed',
                'message': message,
                'sticky': False,
                'type': 'danger',
            }
        }
        return res

    @staticmethod
    def strip_markdown(md: str) -> str:
        html = markdown.markdown(md)

        soup = BeautifulSoup(html, features='html.parser')

        return soup.get_text()

    def update_customer_data(self):

        def get_service_type():
            service_type = False
            if self.service_type_id.is_delivery_service:
                service_type = 'delivery'
            elif self.service_type_id.is_qshop_service:
                service_type = 'qwqershop'
            elif self.service_type_id.is_fleet_service:
                service_type = 'vehicle_deployment'
            return service_type

        def get_customer_segment(segment_id):
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
            if segment_id:
                segment_name = self.segment_id.name
                if segment:
                    return segment.get(segment_name)

        data = {
            'phone': self.phone or False,
            "mobile": self.mobile or False,
            'ref': self.ref or False,
            'comment':  self.strip_markdown(self.comment) if self.comment else False,
            'state_id': self.state_id.l10n_in_tin or False,
            'street': self.street or False,
            'street2': self.street2 or False,
            'city': self.city or False,
            'contact_designation':self.contact_designation or False,
            'country_id': self.country_id.code or False,
            'source_lead_type_id': self.source_lead_type_id.name or False,
            'industry_id': self.industry_id.name,
            'potential_orders_id': self.potential_orders_id.name or False,
            'delivery_type_id': self.delivery_type_id.name or False,
            'service_type_id': get_service_type() or False,
            'segment_id': get_customer_segment(self.segment_id) or False,
            'followup_status_id': self.followup_status_id.name,
            'merchant_amount_collection': self.merchant_amount_collection or False,
            'amount_collection_limit': self.amount_collection_limit or None,
            'collection_charges': self.collection_charges or None,
            'settlement_time_id': self.settlement_time_id.name or None,
            'payment_mode_ids': [mode.code for mode in self.payment_mode_ids] or False,
            'pricing_model': self.pricing_model or False,
            'zip': self.zip or False,
            'vat': self.vat or False,
            'l10n_in_pan': self.l10n_in_pan or False,
            'customer_type': 'retail' if self.customer_type == 'b2c' else self.customer_type or False ,
            'order_sales_person': self.order_sales_person.work_email or False,
            'pricing_type': self.pricing_type or False,
            'sms_alert': self.sms_alert or False,
            'pick_up_area': self.pick_up_area or False,
            'distance_limitation': self.distance_limitation or False,
            'api_selection': self.api_selection or False,
            'product_storage': self.product_storage or False,
            'product_sorting': self.product_sorting or False,
            'email_alert': self.email_alert or False,
            'product_line_id': self.product_line_id.name or False,
            "virtual_bank_acc": self.virtual_bank_acc or False,
            "is_wallet_active": self.is_wallet_active or False,
            "tds_threshold_check": self.tds_threshold_check or False,
            "account_no": self.account_no or False,
            "ifsc_code": self.ifsc_code or False,
            "beneficiary": self.beneficiary or False,
            "bank_name": self.bank_name or False,
            "is_fifo_flow": self.is_fifo_flow or False,
            "max_no_de": self.max_no_de or False,
            "region_id": self.region_id.region_code or False,
            "state_region_id": self.region_id.state_id.code or False,
            "property_payment_term_id": self.property_payment_term_id.name or False,
            "property_product_pricelist": self.property_product_pricelist.name or False,
            "property_supplier_payment_term_id": self.property_supplier_payment_term_id.name or False,
            "property_account_position_id": self.property_account_position_id.name or False,
            "property_stock_customer": self.property_stock_customer.name or False,
            "property_stock_supplier": self.property_stock_supplier.name or False,
            "b2b_invoice_tax_ids": [tax_id.name for tax_id in self.b2b_invoice_tax_ids],
            "b2b_sale_order_tax_ids": [tax_id.name for tax_id in self.b2b_sale_order_tax_ids] or False,
            "qshop_invoice_tax_ids": [tax_id.name for tax_id in self.qshop_invoice_tax_ids] or False,
            "qshop_sale_order_tax_ids": [tax_id.name for tax_id in self.qshop_sale_order_tax_ids] or False,
            "vehicle_invoice_tax_ids": [tax_id.name for tax_id in self.vehicle_invoice_tax_ids] or False,
            "fleet_hsn_id": [hsn_id.name for hsn_id in self.fleet_hsn_id] or False,
            "invoice_frequency_id": self.invoice_frequency_id.name or False,
            'child_ids': [{'type': child.type or False,
                          'name': child.name or False,
                          'street': child.street or False,
                          'email': child.email or False,
                          'phone': child.phone or False,
                          'mobile': child.mobile or False,
                          } for child in self.child_ids] or False,
            'bank_ids': [{'bank_id': bank.bank_id.bic or False,
                          'acc_number': bank.acc_number or False
                          } for bank in self.bank_ids] or False,
            'documents': [{'document_name': doc.document_name or False,
                          'file_name': doc.file_name or False,
                          'file': base64.b64encode(doc.file).decode('utf-8') if doc.file else False
                          } for doc in self.document_ids] or False
        }

        pricing_plan = False
        if self.pricing_model == 'KM':
            pricing_plan = [
                {
                    'from_weight': km_line.minimum_weight or False,
                    'to_weight': km_line.maximum_weight or False,
                    'min_distance': km_line.min_distance or False,
                    'min_cost': km_line.min_cost or False,
                    'per_km_charge': km_line.per_km_charge or False,
                    'km_plan_id': km_line.id or False,
                    'is_original_record': True
                } for km_line in self.km_pricing_plan_ids
            ]
        elif self.pricing_model == 'flat':
            pricing_plan = [
                {
                    'from_weight': flat_line.minimum_weight or False,
                    'to_weight': flat_line.maximum_weight or False,
                    'price': flat_line.price or False
                }for flat_line in self.flat_pricing_plan_ids
            ]
        elif self.pricing_model == 'slab':
            pricing_plan = [
                {
                    'from_distance': slab_line.from_distance or False,
                    'to_distance': slab_line.to_distance or False,
                    'from_weight': slab_line.minimum_weight or False,
                    'to_weight': slab_line.maximum_weight or False,
                    'price': slab_line.price or False
                } for slab_line in self.slab_pricing_plan_ids
            ]
        if pricing_plan:
            data['pricing_plan'] = pricing_plan

        data['additional_charge'] = [
            {
                'charge_type_id': charge.charge_type_id.name or False,
                'amount_type': charge.amount_type or False,
                'amount': charge.amount or False
            } for charge in self.additional_charges_ids
        ] or False

        return data

    def sync_partner_master(self):
        api_datails = self.env['create.api.details']
        api_credentials = self.env['qwqer.api.credentials'].sudo().search([], limit=1)
        if api_credentials and api_credentials.is_partner_update:
            customer_update_data = self.update_customer_data()
            if customer_update_data:
                msg = True
                vals = {"params": customer_update_data}
                headers = {
                    'SecretKey': api_credentials.authorization,
                    'content-type': "application/json",
                }
                url = api_credentials.server_url + '/api/update/customers'
                try:
                    response = requests.request("POST", url, json=vals,
                                                headers=headers)
                    response_data = response.json()['result']
                    data = json.loads(response_data)
                    if data['status_code'] == 200:
                        details = {
                            "api_name": "Customer Update Api",
                            "data": vals,
                            "status": "success",
                            "response": data
                        }
                        msg = self.update_success_notify(data.get('msg') or 'Updated Successfully')
                    else:
                        details = {
                            "api_name": "Customer Update Api",
                            "data": vals,
                            "status": "failed",
                            "response": data
                        }
                        msg = self.updatet_failed_notify(data.get('msg') or 'Updated Failed')
                    api_datails.create(details)
                    return msg

                except Exception as e:
                    _logger.info("Error :exception happened : %s", e)
                    details = {
                        "api_name": "Customer Update Api",
                        "data": vals,
                        "status": "failed",
                        "response": e
                    }
                    api_datails.create(details)
                return msg

            else:
                details = {
                    "api_name": "Customer Update Api",
                    "status": "failed",
                    "response": "data not generated"
                }
                api_datails.create(details)
                return self.updatet_failed_notify('Update Failed')
        else:
            msg = "Credentials not added or not enabled the Partner Update"
            _logger.info(msg)
            return self.updatet_failed_notify(msg)

    def bulk_sync_partner_master(self):
        if len(self.ids) > 50:
            raise ValidationError('Bulk sync Limit is 50 , only 50 records can be proccsses at a time')
        for rec in self:
            sync = rec.sync_partner_master()
            params = sync.get('params', {})
            if params.get('type') == 'danger':
                params['message'] = f"{params.get('message')} for {rec.name}"
                return sync
        return self.update_success_notify('Updated Successfully')

