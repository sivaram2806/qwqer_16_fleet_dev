# coding=utf-8
import json
import logging
import pytz
import datetime
from odoo import fields, http
from datetime import datetime
from odoo.http import request

_logger = logging.getLogger(__name__)
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError
from psycopg2.errors import UniqueViolation


class SaleOrderController(http.Controller):

    @http.route(['/internal/service/request/', '/qshop/service/request/'], type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def service_request(self, api_raw_log=None, **kwargs):
        qshop_api = True if "qshop" in request.httprequest.base_url else False
        service_type_domain = [('is_qshop_service', '=', True)] if qshop_api else [('is_delivery_service', '=', True)]
        service_type_id = request.env["partner.service.type"].search(service_type_domain, limit=1)
        params = {k: (False if v is None else v) for k, v in kwargs.items()}
        _logger.info("Sale Service API : Request Received, Processing ... Time : %s", fields.datetime.now())
        try:
            if not params.get('customer_type'):
                raise APIError(status="REJECTED", status_code=500, message='Mandatory Parameter Customer Type Missing')
            if not params.get('customer_id'): 
                raise APIError(status="REJECTED", status_code=500, message='Mandatory Parameter Customer ID Missing')
            response = self.create_sale_order_and_related_records(params, service_type_id)
            api_raw_log.update({"response": json.dumps(response),
                                'response_date': fields.Datetime.now(),
                                'name': "Sale Order Creation",
                                'key': params.get('order_id',False),
                                'status': response['status']})
            return json.dumps(response)
        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name="Sale Order Creation")
        except Exception as e:
            _logger.error(f"Sale Service API : No Data Received or Incorrect Data Format!{str(e)}")
            error = APIError(status="error", status_code=500,
                             message="An unexpected error occurred. Please try again later")
            response = error.to_response(api_raw_log=api_raw_log, name="Sale Order Creation")
            return response

    def create_sale_order_and_related_records(self, params, service_type_id):
        sale_order = request.env['sale.order']
        so_create_vals = {}
        so_update_vals = {}
        region_state_journal = False
        if 'region' in params:
            region_val = self.validate_and_fetch_region(params['region'], request.env.company.id)
            so_create_vals.update({'region_id': region_val.id or False,
                                    'analytic_account_id': region_val.analytic_account_id.id or False})
            so_update_vals.update({'region_id': region_val.id or False,
                                      'analytic_account_id': region_val.analytic_account_id.id or False})
            region_state_journal = request.env['state.journal'].search([('state_id', '=', region_val.state_id.id)])
        if 'order_status' in params:
            order_status_val = self.validate_and_fetch_order_status(params['order_status'])
            so_create_vals.update({'order_status_id': order_status_val.id or False})
            so_update_vals.update({'order_status_id': order_status_val.id or False})

        if params.get('payment_mode', False):
            payment_mode_id = request.env['payment.mode'].search([('code', '=', params.get('payment_mode', False))])
            if payment_mode_id:
                so_create_vals.update({'payment_mode_id': payment_mode_id.id or False})
                so_update_vals.update({'payment_mode_id': payment_mode_id.id or False})
                is_wallet_payment_mode = payment_mode_id.is_wallet_payment
            else:
                _logger.debug("Service API : Missing Payment Mode for Order ID %s",
                              params.get('order_id', False))
                raise APIError(status="REJECTED", status_code=500, message='Missing Payment Mode')
        else:
            _logger.debug("Service API : Missing Payment Mode for Order ID %s",
                          params.get('order_id', False))
            raise APIError(status="REJECTED", status_code=500, message='Missing Payment Mode')
        order_status = request.env['order.status'].browse(so_create_vals['order_status_id'])


        if params.get('merchant_payment_mode', False):
            merchant_mode_val = request.env['payment.mode'].search([('code', '=', params.get('merchant_payment_mode', False))])
            if merchant_mode_val:
                so_create_vals.update({'merchant_payment_mode_id': merchant_mode_val.id or False})
                so_update_vals.update({'merchant_payment_mode_id': merchant_mode_val.id or False})

        datetime_fields = {
            'order_date_time': {'msg': 'Invalid Order Date Format', 'filed_mapping': 'order_date'},
            'order_accepted_date_time': {'msg': 'Invalid Order Accepted Date Format',
                                         'filed_mapping': 'order_accepted_date'},
            'order_picked_up_date_time': {'msg': 'Invalid Order Picked Up Date Format',
                                          'filed_mapping': 'order_picked_up_date'},
            'order_delivered_date_time': {'msg': 'Invalid Order Delivered Date Format',
                                          'filed_mapping': 'order_delivered_date'},
        }
        for field, filed_value in datetime_fields.items():
            if params.get(field):
                parsed_date = self._parse_datetime_field(params[field], filed_value['msg'])
                so_create_vals[filed_value['filed_mapping']] = parsed_date
                so_update_vals[filed_value['filed_mapping']] = parsed_date

        so_create_vals['date_order'] = so_create_vals['order_date']
        so_update_vals['date_order'] = so_update_vals['order_date']

        time_fields = ['time_to_accept', 'time_to_pickup', 'time_to_deliver', 'overall_order_time',
                       'estimated_time']
        for field in time_fields:
            time_val = self._parse_time_field(params.get(field))
            if time_val is not None:
                so_create_vals[field] = time_val
                so_update_vals[field] = time_val
        yes_or_no_fields = ['scheduled']
        for field in yes_or_no_fields:
            yes_or_no_val = 'yes' if (params.get(field) and isinstance(params.get(field), str) and
                                      params.get(field).lower() in ["y", "yes", "true"]) else 'no'
            if yes_or_no_val is not None:
                so_create_vals[field] = yes_or_no_val
                so_update_vals[field] = yes_or_no_val
        sla_keys = ['accept_sla', 'pickup_sla', 'delivery_sla']
        self.update_sla_values(params, sla_keys, so_create_vals, so_update_vals)

        if 'stop_count' in params:
            stop_count = params.get('stop_count', False)
            if stop_count:
                so_create_vals.update({'stop_count': str(stop_count) or False})
                so_update_vals.update({'stop_count': str(stop_count) or False})

        common_fields_mapping = {
            'order_id': 'order_id',
            # 'order_date_time': 'date_order',
            'order_amount': 'order_amount',
            'discount_amount': 'discount_amount',
            # 'estimated_time': 'estimated_time',
            'amount': 'total_amount',
            'promo_code': 'promo_code',
            'payment_id': 'payment_id',
            'merchant_order_amount': 'merchant_order_amount',
            'estimated_distance': 'estimated_distance',
            'pickup_distance': 'pickup_distance',
            'deliver_distance': 'deliver_distance',
            'weight': 'weight',
            'item_type': 'item_type',
            'description': 'description',
            'from_name': 'from_name',
            'from_phone_no': 'from_phone_no',
            'from_address': 'from_address',
            'sender_locality': 'sender_locality',
            'from_postal_code': 'from_postal_code',
            'to_name': 'to_name',
            'to_phone_no': 'to_phone_no',
            'to_address': 'to_address',
            'receiver_locality': 'receiver_locality',
            'to_postal_code': 'to_postal_code',
            'driver_name': 'driver_name',
            'driver_phone': 'driver_phone',
            'driver_rating': 'driver_rating',
            'driver_comment': 'driver_comment',
            'order_source': 'order_source',
            'cancellation_comments': 'cancellation_comments',
            'customer_rating': 'customer_rating',
            'customer_feedback': 'customer_feedback',
            'customer_comment': 'customer_comment',
            'special_instruction': 'special_instruction',
            'stop_count': 'stop_count',
            'stop_details': 'stop_details',
            'payment_status': 'payment_status',
            'merchant_order_id': 'merchant_order_id',
        }
        if service_type_id.is_qshop_service:
            common_fields_mapping.update({'promo_desc': 'promo_desc', 
                                          'merchant_total_amount': 'merchant_total_amount',
                                          'merchant_discount_amount': 'merchant_discount_amount'}
                                          )
        for param_key, field_name in common_fields_mapping.items():
            param_value = params.get(param_key) or params.get(param_key)
            if param_value is not None:
                so_create_vals[field_name] = param_value
                so_update_vals[field_name] = param_value
        if is_wallet_payment_mode:
            if 'erp_wallet_trans_id' in params:
                moves = False
                wallet_trans_id = params.get('erp_wallet_trans_id')
                order_id = params.get('order_id')
                if wallet_trans_id:  # When wallet transaction ID is provided
                    moves = request.env['account.move'].search([('wallet_order_id', '=', order_id),
                                                                ('name', '=', wallet_trans_id), ('state', '=', 'posted')
                                                                ], limit=1)
                    if not moves:
                        moves_line = request.env['account.move.line'].search([('wallet_order_id', '=', order_id),
                                                                              ('move_id.name', '=', wallet_trans_id),
                                                                              ('move_id.state', '=', 'posted')], limit=1)
                        moves = moves_line.move_id
                        #TODO to handle 13 to 16 sync, once it stopped remove search without name
                        if not moves:
                            moves = request.env['account.move'].search([('wallet_order_id', '=', order_id),
                                                                        ('state', '=', 'posted')
                                                                        ], limit=1)
                            if not moves:
                                moves_line = request.env['account.move.line'].search(
                                    [('wallet_order_id', '=', order_id),
                                     ('move_id.state', '=', 'posted')], limit=1)
                                moves = moves_line.move_id
                else:  # Handle cases with missing transaction ID and canceled orders
                    if order_status.is_cancel_order:
                        existing_sale_order = sale_order.search([('order_id', '=', so_create_vals['order_id'])],
                                                                limit=1)
                        if not existing_sale_order:
                            moves = request.env['account.move'].search([('wallet_order_id', '=', order_id),
                                                                        ('state', '=', 'posted')], limit=1)

                if moves:
                    if service_type_id.is_delivery_service or  not moves.has_reconciled_entries:
                        so_create_vals.update({'wallet_move_id': moves.id or False})
                    else:
                        moves = request.env['account.move'].sudo().search(
                            [('wallet_order_id', '=', params.get('order_id', False))
                                , ('state', '=', 'posted'), ('is_wallet_merchant_journal', '=', False),
                             ])
                        un_reconcile_wallet_entry = moves.filtered(
                            lambda s: not s.has_reconciled_entries)
                        if un_reconcile_wallet_entry:
                            so_create_vals.update({'wallet_move_id': un_reconcile_wallet_entry.id or False})
                else:
                    if not order_status.is_cancel_order:
                        raise APIError(status="REJECTED", status_code=500, message='Missing Wallet Transaction Entry',
                                       additional_params={
                            'order_id': params.get('order_id', False) or "",
                            'erp_wallet_trans_ref_id': params.get('erp_wallet_trans_id', False)})
                    
        if service_type_id.is_delivery_service and 'pricing_plan' in params:
            pricing_plan = params.get('pricing_plan', False)
            if pricing_plan:
                so_create_vals.update({'pricing_plan': pricing_plan or False})
                so_update_vals.update({'pricing_plan': pricing_plan or False})
        if service_type_id.is_qshop_service and 'products' in params:
            products = params.get('products', False)
            lines = []
            for q in products:
                if q.get('sku', False):
                    lines.append((0,0, {
                        'name': q.get('sku', False),
                        'item_name': q.get('name', False),
                        'weight': q.get('weight', False),
                        'units': q.get('units', False),
                        'sell_price': q.get('price', False),
                        'mark_price': q.get('mrp', False),
                        'total_price': q.get('total', False),
                    }))
                else:
                    raise APIError(status="REJECTED", status_code=500, message='Missing Product SKU')
            so_create_vals.update({'qshop_product_line': lines or False})

        if 'charges' in params:
            charges = params.get('charges', False)
            if charges:
                for charge_key, charge_val in charges.items():
                    if not isinstance(charge_val, (int, float)):
                        raise APIError(status="REJECTED", status_code=500,
                                       message=f"Error '{charge_key}':'{charge_val}' All charges Sub Field Value Should be a Number")
                so_create_vals.update({'charges': charges or False})
                so_update_vals.update({'charges': charges or False})

        driver = False
        if 'driver_id' in params:
            driver_id = params.get('driver_id', False)
            if driver_id:
                driver = request.env['hr.employee'].search([('driver_uid', '=', driver_id)])
                if driver:
                    so_create_vals.update({'driver_id': driver.id or False,
                                           'driver_uid': driver_id or False})
                    so_update_vals.update({'driver_id': driver.id or False,
                                           'driver_uid': driver_id or False})
                    if not driver.related_partner_id:
                        raise APIError(status="REJECTED", status_code=500, message='Related partner is missing for the Driver')
                    if not driver.journal_id:
                        raise APIError(status="REJECTED", status_code=500, message='Journal is missing')
                else:
                    raise APIError(status="REJECTED", status_code=500, message='Driver ID Not Available')
            else:
                order_status = request.env['order.status'].browse(so_create_vals['order_status_id'])

                if not driver_id and order_status.is_cancel_order == False:
                    raise APIError(status="REJECTED", status_code=500, message='Driver ID Not Available')
        if service_type_id.is_qshop_service:
            self.get_billing_partner_id(params, payment_mode_id, so_create_vals)
        if 'customer_type' in params and 'customer_id' in params:
            customer_type = params.get('customer_type')
            customer_id = params.get('customer_id')
            partner = None
            if customer_type == 'B2B':
                partner = request.env['res.partner'].search([('customer_ref_key', '=', customer_id),
                                                             ('customer_type', '=', 'b2b')])
                if len(partner) > 1:
                    raise APIError(status="REJECTED", status_code=500, message='Duplicate Customer')
                elif not partner:
                    raise APIError(status="REJECTED", status_code=500, message='Missing Customer')

            elif customer_type == 'B2C':
                if len(customer_id) > 13:
                    raise APIError(status="REJECTED", status_code=500, message='Customer ID exceeds length')
                partner = request.env['res.partner'].search([('phone', '=', params.get('customer_id')),
                                                             ('customer_type', '=', 'b2c')])
                if len(partner) > 1:
                    raise APIError(status="REJECTED", status_code=500, message='Duplicate Customer')
                if not partner:
                    partner = request.env['res.partner'].create({
                        'name': params.get('customer_name', False),
                        'phone': params.get('customer_id'),
                        'customer_type': 'b2c',
                        'state_id': region_val.state_id.id,
                        'region_id': so_create_vals['region_id'],
                        'customer_rank': 1,
                    })
                    _logger.info("Service API: Created Customer %s for Order ID %s", partner.id, params.get('order_id'))

            if partner:
                so_create_vals.update({
                    'partner_id': partner.id,
                    'order_sales_person': partner.order_sales_person.id if partner.order_sales_person else False
                })
        else:
            raise APIError(status="REJECTED", status_code=500, message='Mandatory Parameter Customer ID Missing')
        product = request.env.company.qwqer_shop_product_id if service_type_id.is_qshop_service else request.env.company.product_id
        if not product:
            _logger.info("Service API : Product for Order Id %s not found",
                         params.get('order_id', False))

        state_journal = request.env['state.journal'].search([('state_id', '=', partner.state_region_id.id)])

        if not state_journal:
            _logger.info("Service API : Journal for Order Id %s not found",
                         params.get('order_id', False))

        tax_list = []
        if partner.customer_type == 'b2b' and service_type_id.is_qshop_service:
            for b2b_tax in partner.qshop_sale_order_tax_ids:
                tax_list.append(b2b_tax)
        elif partner.customer_type == 'b2b':
            for b2b_tax in partner.b2b_sale_order_tax_ids:
                tax_list.append(b2b_tax)
        elif partner.customer_type == 'b2c':
            if region_state_journal:
                for b2c_tax in region_state_journal.tax_b2c_sale_order:
                    tax_list.append(b2c_tax)
            else:
                for b2c_tax in state_journal.tax_b2c_sale_order:
                    tax_list.append(b2c_tax)
        if payment_mode_id.is_credit_payment and service_type_id.is_qshop_service:
            so_create_vals.update({'billing_partner_id': partner.id or False})

        so_create_vals.update(
            {'order_line': [
                (0, 0, {'product_id': product.id,
                        'name': product.name,
                        'price_unit': params.get('amount'),
                        'tax_id': [(4, i.id) for i in tax_list],
                        'service_type_id': service_type_id.id
                        }
                 )],
             'l10n_in_journal_id': state_journal.qshop_journal_id.id if service_type_id.is_qshop_service else state_journal.delivery_journal_id.id,
             # 'is_service_details': True,
             }
        )

        order_status = request.env['order.status'].browse(so_create_vals['order_status_id'])

        if not driver and order_status.is_cancel_order == False:
            _logger.info("Service API : Driver ID not available for Order ID %s",
                         params.get('order_id', False))
            raise APIError(status="REJECTED", status_code=402, message='Driver ID Not Available')

        if not order_status.is_cancel_order:
            so_create_vals.update({'state': 'sale'})
        else:
            so_create_vals.update({'state': 'cancel'})
        existing_order = sale_order.search([('order_id', '=', so_create_vals['order_id'])], limit=1)

        if existing_order and service_type_id.is_qshop_service:
            if existing_order.partner_id.id != partner.id:
                raise APIError(status="REJECTED", status_code=500, message='Customer Mismatch for Existing Order')
        so_create_vals.update({'service_type_id': service_type_id.id})
        so_update_vals.update({'service_type_id': service_type_id.id})
        order_id = params.get('order_id', False)
        # When payment method is changed invoice is cancelled in the case of payment mode is equal to Online or Credit
        # and a new invoice is created. If the payment mode is COD/COP and changed to COP/COD respectively then invoice
        # is updated without cancelling the existing invoice.

        existing_order = sale_order.search([('order_id', '=', so_create_vals['order_id'])], limit=1)
        payment_mode = str(params.get('payment_mode', False))
        merchant_payment_mode = str(params.get('merchant_payment_mode', False)) if params.get('merchant_payment_mode',
                                                                                              False) else False
        if existing_order:
            if existing_order.order_status_id.code != "5":
                if existing_order.payment_mode_id.code != payment_mode:
                    inv_ids = existing_order.invoice_ids.filtered(lambda s: s.state in ['draft', 'posted'])
                    for inv in inv_ids:
                        if existing_order.payment_mode_id.code == '5' and payment_mode != '5' and not inv.consolidated_invoice_id:
                            existing_order.reverse_credit_sale_journal()
                        elif existing_order.payment_mode_id.code == '5' and payment_mode != '5' and inv.consolidated_invoice_id:
                            raise APIError(status="REJECTED", status_code=500,
                                           message='Payment mode cannot be changed since Invoice is already generated for the respective order')
                    for inv in inv_ids:
                        if inv:

                            # checking if e-invoice is already created against the existing sale order. If then,
                            # we are returning a response and restricting to create or make any change in the existing
                            # invoice

                            if inv.einvocie_details_ids and inv.einvocie_details_ids[0].irn:

                                raise APIError(status="REJECTED", status_code=500,
                                               message='Payment mode cannot be changed since E-Invoice is already generated for the respective order')

                            # if the existing payment mode is COP/COD and the new payment mode is changed to COD/COP,
                            # invoice is updated with the new payment mode.

                            elif payment_mode in ['1', '3'] and existing_order.payment_mode_id.code in ['1', '3']:
                                inv.sudo().payment_mode_id = payment_mode_id.id
                            else:
                                inv.sudo().with_context({'from_api': True}).button_draft()
                                if inv.sudo().state == 'draft':
                                    existing_order.payment_mode_id = payment_mode_id.id
                                    inv.sudo().with_context({'from_api': True}).button_cancel()
                                    inv.sudo().with_context({'from_api': True}).update_sale_order_status()
                                if payment_mode != '5':
                                    if inv.sudo().state == 'cancel':
                                        self.create_invoice(existing_order)

                # When merchant payment method is changed merchant journal is cancelled in the case of merchant
                # payment mode is equal to Online and a new merchant journal is created. If the payment mode is
                # COD/COP and changed to COP/COD respectively then merchant journal
                # is updated without cancelling the existing invoice.

                if existing_order.merchant_order_amount > 0 and existing_order.merchant_journal_ids:
                    if merchant_payment_mode and existing_order.merchant_payment_mode_id.code != merchant_payment_mode:
                        move_id = existing_order.merchant_journal_ids[0].move_id
                        if not existing_order.merchant_journal_ids.filtered(lambda s: s.full_reconcile_id):

                            # if the existing merchant payment mode is COP/COD and the new merchant payment mode is
                            # changed to COD/COP, no change is done.

                            if merchant_payment_mode in ['1', '3'] and existing_order.merchant_payment_mode_id.code in [
                                '1', '3']:
                                pass

                            # if the existing merchant payment mode is COP/COD and the new merchant payment mode is
                            # changed to COD/COP, existing merchant journal is cancelled and new merchant journal is
                            # created with new merchant payment mode.

                            else:
                                move_id.sudo().with_context(
                                    {'from_api': True}).button_draft()
                                if move_id.sudo().state == 'draft':
                                    move_id.sudo().with_context({'from_api': True}).button_cancel()
                                if move_id.sudo().state == 'cancel':
                                    so_update_vals.update({'is_merchant_journal': False})
                                    existing_order.with_context({'from_api': True}).write(so_update_vals)
                                merchant_config = request.env['merchant.journal.data.configuration'].sudo().search([],
                                                                                                          limit=1)
                                if merchant_config:
                                    self.merchant_journal_mapping(existing_order)
                                    so_update_vals.update({'is_merchant_journal': True})
                                    existing_order.with_context({'from_api': True}).write(so_update_vals)
                        else:
                            raise APIError(status="REJECTED", status_code=500, message='Merchant Payout is already done')

            # if existing_order:
            if existing_order.partner_id.id != partner.id:
                _logger.info("Service API : Customer Mismatch for Existing Order ID %s", params.get('order_id', False))
                raise APIError(status="REJECTED", status_code=500, message='Customer Mismatch for Existing Order')
        new_order = False
        if params.get('customer_type') == 'B2B':
            if existing_order:
                if order_status.is_cancel_order:
                    self.cancel_invoices(existing_order)
                    so_update_vals.update({'state': 'cancel'})
                    existing_order.with_context({'from_api': True}).write(so_update_vals)
                    self.update_merchant_and_credit_journals(existing_order)
                    _logger.info("Service API : B2B Order %s and associated invoices canceled.",
                                 existing_order.order_id)
                    msg = "Existing B2B Order and Invoices Cancelled, Order Updated"
                else:
                    so_update_vals.update({'state': 'sale'})
                    existing_order.with_context({'from_api': True}).write(so_update_vals)
                    self.update_merchant_and_credit_journals(existing_order)
                    if existing_order.invoice_status == 'to invoice' and existing_order.state == 'sale' and existing_order.payment_mode_id.code != "5":
                        self.create_invoice(existing_order)
                        msg = "Existing B2B Order Updated and Invoice Created"
                    else:
                        msg = "Existing B2B Order Updated"
            else:
                new_order, msg = self.create_new_order_and_journals(so_create_vals)
            _logger.info("Service API : %s", msg)

        if params.get('customer_type') == 'B2C':
            if existing_order:
                msg = self.handle_existing_b2c_order(existing_order, order_status, so_update_vals)
            else:
                new_order, msg = self.handle_new_b2c_order(so_create_vals)
        status_code = 200
        reponse_order_id = ''
        response_sale_order_id = ''
        erp_wallet_trans_ref_id = ''

        if existing_order:
            existing_order.onchange_driver_id()
            self._set_onchange_partner_id(existing_order)
            response_sale_order_id = existing_order.name
            erp_wallet_trans_ref_id = existing_order.sudo().wallet_move_id.name # TODO
        elif new_order:
            new_order.onchange_driver_id()
            self._set_onchange_partner_id(new_order)
            response_sale_order_id = new_order.name
            erp_wallet_trans_ref_id = new_order.sudo().wallet_move_id.name # TODO
        return {
            'order_id': reponse_order_id,
            'sale_order_id': response_sale_order_id,
            'erp_wallet_trans_ref_id': erp_wallet_trans_ref_id,
            'status_code': status_code,
            'status': "SUCCESS",
            'msg': msg,
        }

    def _set_onchange_partner_id(self, order):
        for rec in order:
            if rec.partner_id:
                field_map = {
                    'region_id': 'region_id',
                    'order_sales_person': 'order_sales_person',
                    'partner_invoice_id': 'id',
                    'partner_shipping_id': 'id',
                    'service_type_id': 'service_type_id',
                    'industry_id': 'industry_id',
                    'customer_segment_id': 'segment_id',
                    'product_line_id': 'product_line_id',
                }
                for field, partner_field in field_map.items():
                    if not getattr(rec, field):
                        setattr(rec, field, getattr(rec.partner_id,
                                                    partner_field).id if partner_field != 'id' else rec.partner_id.id)
            rec.is_qshop_service = rec.service_type_id.is_qshop_service

    @staticmethod
    def cancel_invoices(existing_order):
        """Cancel invoices for the given existing order."""
        _logger.info("Service API : Getting Invoices for Order ID %s, Time : %s",
                     existing_order.order_id, fields.datetime.now())
        inv_ids = existing_order.invoice_ids.filtered(lambda s: s.state in ['draft', 'posted'])
        for inv in inv_ids:
            if existing_order.payment_mode_id.code != "5":
                try:
                    inv.sudo().with_context({'from_api': True}).button_cancel()
                except Exception as e:
                    raise APIError(status="REJECTED", status_code=500, message=str(e))
            else:
                raise APIError(status="REJECTED", status_code=500,
                               message='Invoice already generated for B2B Sale order with credit payment')
        _logger.info("Service API : Cancelled invoices for Order ID %s, Time : %s",
                     existing_order.order_id, fields.datetime.now())


    def update_merchant_and_credit_journals(self, existing_order):
        """Update merchant and credit journals for the existing order."""
        merchant_config = request.env['merchant.journal.data.configuration'].sudo().search([], limit=1)
        if not merchant_config:
            raise APIError(status="REJECTED", status_code=500,
                           message='Missing Journal for the customer in merchant amount configuration')

        _logger.info("Service API : Updating Merchant journal for Order ID %s, Time : %s",
                     existing_order.order_id, fields.datetime.now())
        self.merchant_journal_mapping(existing_order)

        if existing_order.payment_mode_id.code == "5":
            _logger.info("Service API : Updating Credit journal for Order ID %s, Time : %s",
                         existing_order.order_id, fields.datetime.now())
            self.existing_credit_journal_mapping(existing_order)


    def create_new_order_and_journals(self, so_create_vals):
        """Create a new B2B order and handle its journals."""
        try:
            new_order = request.env['sale.order'].create(so_create_vals)
            msg = "New B2B Order Created"
        except UniqueViolation:
            raise APIError(status="REJECTED", status_code=500,
                           message=f"Record already exists with order_id: {so_create_vals['order_id']}")
        except Exception as e:
            raise APIError(status="REJECTED", status_code=500, message=str(e))

        _logger.info("Service API : Created New B2B Order ID %s, Time: %s", new_order.order_id, fields.datetime.now())
        if new_order.state == 'sale' and new_order.payment_mode_id.code != "5":
            self.create_invoice(new_order)
            _logger.info("Service API : Created Invoice for B2B Order ID %s, Time %s", new_order.order_id, fields.datetime.now())

        if new_order.payment_mode_id.code == "5" and new_order.order_status_id.code !="5":
            new_order.create_credit_order_journal()
            msg = "New B2B Order and Invoice Created"
        if new_order.merchant_order_amount > 0 and new_order.order_status_id.code == "4":
            merchant_config = request.env['merchant.journal.data.configuration'].sudo().search([], limit=1)
            if merchant_config:
                if new_order.service_type_id.is_qshop_service:
                    new_order.create_qwqer_shop_merchant_journal()
                if new_order.service_type_id.is_delivery_service: 
                    new_order.create_delivery_merchant_journal()
            else:
                raise APIError(status="REJECTED", status_code=500,
                               message="Missing Journal for the customer in merchant amount configuration")
        return new_order, msg

    def handle_existing_b2c_order(self, existing_order, order_status, so_update_vals):
        """Handle updates or cancellations for an existing B2C order."""
        if order_status.is_cancel_order:
            self.cancel_b2c_order(existing_order, so_update_vals)
            return "Existing B2C Order Cancelled"
        else:
            return self.update_b2c_order(existing_order, so_update_vals)

    def cancel_b2c_order(self, existing_order, so_update_vals):
        """Cancel an existing B2C order and its related invoices."""
        _logger.info("Service API: Cancelling invoices for Order ID %s, Time: %s",
                     existing_order.order_id, fields.datetime.now())

        self.cancel_invoices(existing_order)

        so_update_vals.update({'state': 'cancel'})
        existing_order.update(so_update_vals)

        _logger.info("Service API: Sale order cancelled for Order ID %s, Time: %s",
                     existing_order.order_id, fields.datetime.now())

        self.ensure_merchant_journal(existing_order, "Service API: Merchant Journal Update")

    def update_b2c_order(self, existing_order, so_update_vals):
        """Update an existing B2C order and handle related processes."""
        _logger.info("Service API: Updating sale order for Order ID %s, Time: %s",
                     existing_order.order_id, fields.datetime.now())

        so_update_vals.update({'state': 'sale'})
        existing_order.update(so_update_vals)

        self.ensure_merchant_journal(existing_order, "Service API: Merchant Journal Update")

        if existing_order.invoice_status == 'to invoice':
            self.create_invoice(existing_order)
            return "Existing B2C Order Updated and Invoice Created"
        return "Existing B2C Order Updated"

    def handle_new_b2c_order(self, so_create_vals):
        """Create a new B2C order and handle subsequent processes."""
        _logger.info("Service API: Creating new B2C order for Order ID %s, Time: %s",
                     so_create_vals['order_id'], fields.datetime.now())

        try:
            new_order = request.env['sale.order'].create(so_create_vals)
        except UniqueViolation:
            raise APIError(status="REJECTED", status_code=500,
                           message=f"Record already exists with order_id: {so_create_vals['order_id']}")
        except Exception as e:
            raise APIError(status="REJECTED", status_code=500, message=str(e))

        _logger.info("Service API: New B2C Order created with ID %s, Time: %s",
                     new_order.order_id, fields.datetime.now())

        msg = self.process_new_b2c_order(new_order)
        return new_order, msg

    def process_new_b2c_order(self, new_order):
        """Handle post-creation tasks for a new B2C order."""
        msg = "New B2C Order Created"
        if new_order.state == 'sale':
            self.create_invoice(new_order)
            msg = "New B2C Order and Invoice Created"
        if new_order.merchant_order_amount > 0 and new_order.order_status_id.code == "4":
            self.ensure_merchant_journal(new_order, "Service API: Merchant Journal Create")
        if new_order.merchant_order_amount > 0 and not new_order.order_status_id.code == "4":
            if new_order.merchant_payment_mode_id.is_wallet_payment:
                # refund merchant amount to wallet
                moves = request.env['account.move'].sudo().search(
                    [('wallet_order_id', '=', new_order.order_id),
                     ('is_wallet_merchant_journal', '=', True), ('state', '=', 'posted')])
                un_reconcile_merch_wallet_entry = moves.filtered(
                    lambda s: not s.has_reconciled_entries)
                if un_reconcile_merch_wallet_entry:
                    new_order.sudo().merchant_wallet_move_id = un_reconcile_merch_wallet_entry.id
                    new_order._reverse_shop_merchant_wallet_entry()
                    _logger.info("Service API : Merchant journal created")
        return msg

    def ensure_merchant_journal(self, order, log_message):
        """Ensure merchant journal entry exists for the order."""
        _logger.info(f"{log_message} for Order ID %s, Time: %s",
                     order.order_id, fields.datetime.now())

        merchant_config = request.env['merchant.journal.data.configuration'].sudo().search([], limit=1)
        if not merchant_config:
            raise APIError(status="REJECTED", status_code=500,
                           message="Missing Journal for the customer in merchant amount configuration")
        if order.service_type_id.is_qshop_service:
            order.create_qwqer_shop_merchant_journal()
        if order.service_type_id.is_delivery_service:
            order.create_delivery_merchant_journal()
        _logger.info("Service API: Merchant journal updated for Order ID %s, Time: %s",
                     order.order_id, fields.datetime.now())

    def _parse_time_field(self, time_str):
        if not time_str:
            return None
        time_parts = time_str.split(",")[-1].strip().split(":")
        if len(time_parts) == 3:
            return int(time_parts[0]) + int(time_parts[1]) / 60 + int(time_parts[2]) / 3600
        return None

    def _parse_datetime_field(self, date_str, error_msg):
        try:
            local = pytz.timezone(request.env.user.tz or pytz.utc)
            naive_date = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
            local_dt = local.localize(naive_date, is_dst=None)
            return local_dt.astimezone(pytz.utc).replace(tzinfo=None)
        except:
            raise APIError(status="REJECTED", status_code=500, message=error_msg)

    @staticmethod
    def create_invoice(order):
        journal = request.env['state.journal'].search([('state_id', '=', order.partner_id.state_id.id)])
        sale_order = request.env['sale.order'].search([('order_id', '=', order.order_id)])

        region_state_journal = request.env['state.journal'].search([('state_id', '=', order.region_id.state_id.id)])
        tax_ids = False
        partner_tax_ids = False
        partner_id = False
        selling_partner_id = False
        if order.partner_id.customer_type == "b2c":
            tax_ids = region_state_journal.tax_b2c_invoice.ids
            partner_tax_ids = journal.tax_b2c_invoice.ids
        if order.service_type_id.is_delivery_service:
            partner_id = order.partner_id
            selling_partner_id = False
            if order.partner_id.customer_type == "b2b":
                tax_ids = order.partner_id.b2b_sale_order_tax_ids.ids
                partner_tax_ids = order.partner_id.b2b_sale_order_tax_ids.ids
        if order.service_type_id.is_qshop_service:
            partner_id = order.billing_partner_id
            selling_partner_id = order.partner_id
            if order.partner_id.customer_type == "b2b":
                tax_ids = order.partner_id.qshop_sale_order_tax_ids.ids
                partner_tax_ids = order.partner_id.qshop_sale_order_tax_ids.ids
        if region_state_journal:
            record = {
                'move_type': 'out_invoice',
                'partner_id': partner_id.id,
                'selling_partner_id': selling_partner_id and selling_partner_id.id,
                'sales_person_id': order.partner_id.order_sales_person.id or False,
                'journal_id': region_state_journal.delivery_journal_id.id,
                'company_id': request.env.user.company_id.id,
                'currency_id': request.env.user.company_id.currency_id.id,
                'invoice_date': fields.Date.context_today(order),
                'state': 'draft',
                'region_id': order.region_id.id,
                'segment_id': order.partner_id.segment_id.id,
                'service_type_id': order.service_type_id.id,
                'customer_type': order.customer_type,
                "driver_id": sale_order.driver_id.id,
                "driver_name": sale_order.driver_name,
                "driver_phone": sale_order.driver_phone,
                "order_id": sale_order.order_id,
                "payment_mode_id": sale_order.payment_mode_id.id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': k.product_id.id,
                    'analytic_distribution': {str(order.analytic_account_id.id): 100.0},
                    'company_id': request.env.user.company_id.id,
                    'currency_id': request.env.user.company_id.currency_id.id,
                    'price_unit': k.price_total,
                    'tax_ids': [(6, 0, tax_ids)]
                }) for k in order.order_line],
                'order_line_ids': [(6, 0, order.ids)]
            }
            try:
                invoice = request.env['account.move'].create(record)
            except Exception as e:
                _logger.info("Service API : Invoice Mapping Failed %s,Order id : %s ,Time : %s", e, sale_order.order_id,
                             fields.datetime.now())

        else:
            try:
                invoice = request.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': order.partner_id.id,
                    'sales_person_id': order.partner_id.order_sales_person.id or False,
                    'journal_id': journal.journal_id.id,
                    'company_id': request.env.user.company_id.id,
                    'currency_id': request.env.user.company_id.currency_id.id,
                    'invoice_date': fields.Date.context_today(order),
                    'state': 'draft',
                    'region_id': order.region_id.id,
                    'segment_id': order.partner_id.segment_id.id,
                    'service_type_id': order.service_type_id.id,
                    'customer_type': order.customer_type,
                    "driver_id": sale_order.driver_id.id,
                    "driver_name": sale_order.driver_name,
                    "driver_phone": sale_order.driver_phone,
                    "payment_mode_id": sale_order.payment_mode_id,
                    "order_id": sale_order.order_id,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': k.product_id.id,
                        'company_id': request.env.user.company_id,
                        'analytic_account_id': order.analytic_account_id.id,
                        'currency_id': request.env.user.company_id.currency_id,
                        'price_unit': k.price_total,
                        'tax_ids': [(6, 0, partner_tax_ids)]
                    }) for k in order.order_line],
                    'order_line_ids': [(6, 0, order.ids)]
                })
            except Exception as e:
                _logger.info("Service API : Invoice Mapping Failed %s,Order id : %s ,Time : %s", e, sale_order.order_id,
                             fields.datetime.now())

        _logger.info("Service API : Invoice Created for Order ID %s", order.order_id)
        for j in invoice.order_line_ids:
            for lines in j.order_line:
                lines.write({'invoice_lines': [(6, 0, invoice.invoice_line_ids.ids)]})
        invoice.is_inv_api_entry = True
        _logger.info("Service API : Invoice Posted for Order ID %s, Time: %s", order.order_id, fields.datetime.now())

    @staticmethod
    def merchant_journal_mapping(sale_order):
        order_status_code = sale_order.order_status_id.code
        if order_status_code == '5' or order_status_code == '6' or order_status_code == '7' or order_status_code == '8':
            if sale_order.is_merchant_journal and sale_order.merchant_order_amount > 0:
                sale_order.reverse_merchant_journal()
                if sale_order.merchant_payment_mode_id.is_wallet_payment:
                    sale_order._reverse_shop_merchant_wallet_entry()
                sale_order.is_merchant_journal = False
        if sale_order.merchant_order_amount > 0 and sale_order.order_status_id.code == "4":
            if not sale_order.is_merchant_journal:
                if sale_order.service_type_id.is_qshop_service:
                    sale_order.create_qwqer_shop_merchant_journal()
                if sale_order.service_type_id.is_delivery_service:
                    sale_order.create_delivery_merchant_journal()
                sale_order.is_merchant_journal = True

    @staticmethod
    def existing_credit_journal_mapping(sale_order):
        order_status_code = sale_order.order_status_id.code
        if sale_order.payment_mode_id.code == "5":
            if order_status_code == '5':
                sale_order.reverse_credit_sale_journal()
                sale_order.is_credit_journal_created = False
            if sale_order.payment_mode_id.code == "5" and order_status_code != "5":
                if not sale_order.is_credit_journal_created:
                    sale_order.create_credit_order_journal()
                    sale_order.is_credit_journal_created = True

    # TODO: qshop all
    @staticmethod
    def validate_and_fetch_region(region_code, company_id):
        """Validate and fetch the region details."""
        region = request.env['sales.region'].search(
            [('region_code', '=', region_code), ('company_id', '=', company_id)], limit=1)
        if not region:
            _logger.debug("Service API: Missing Region Code for Region Code %s", region_code)
            raise APIError(status="REJECTED", status_code=500, message='Missing Region Code')
        return region

    @staticmethod
    def validate_and_fetch_order_status(status_code):
        """Validate and fetch the order status."""
        status = request.env['order.status'].search([('code', '=', status_code)], limit=1)
        if not status:
            _logger.debug("Service API: Missing Order Status for Status Code %s", status_code)
            raise APIError(status="REJECTED", status_code=500, message='Missing Order Status')
        return status

    @staticmethod
    def update_sla_values(params, sla_keys, so_create_vals, so_update_vals):
        """
        Update SLA-related fields in `so_create_vals` and `so_update_vals` based on parameters.
        """
        for sla_key in sla_keys:
            if sla_key in params:
                sla_value = params.get(sla_key, False)
                boolean_value = sla_value == '1'
                so_create_vals.update({sla_key: boolean_value})
                so_update_vals.update({sla_key: boolean_value})

    @staticmethod
    def get_billing_partner_id(params, payment_mode_id, so_create_vals):
        if not payment_mode_id.is_credit_payment:
            to_name = params.get('to_name', False)
            to_phone_no = params.get('to_phone_no', False)
            if to_phone_no:
                length = len(to_phone_no)
                if not length > 10:
                    to_phone_no = f"+91{to_phone_no}"
                billing_partner = request.env['res.partner'].search([('phone', '=', to_phone_no)])
                if len(billing_partner) > 1:
                    raise APIError(status="REJECTED", status_code=500, message='Driver ID Not Available')

                if not billing_partner:
                    if length > 13:
                        raise APIError(status="REJECTED", status_code=500, message='Driver ID Not Available')
                    region = request.env['state.journal'].search([('state_id.regions_ids.region_code', '=', params.get('region'))])
                    billing_partner = request.env['res.partner'].sudo().create({
                        'name': to_name,
                        'phone': to_phone_no,
                        'customer_type': 'b2c',
                        'state_id': region.state_id.id,
                        'region_id': so_create_vals['region_id'],
                        'customer_rank': 1,
                    })
                if billing_partner:
                    so_create_vals.update({'billing_partner_id': billing_partner.id or False})
            else:
                raise APIError(status="REJECTED", status_code=500, message='Missing parameter To Phone Number')
