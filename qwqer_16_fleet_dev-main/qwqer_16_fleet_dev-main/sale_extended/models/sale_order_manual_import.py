# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
import logging

from odoo.exceptions import UserError, ValidationError

from odoo import models, fields, api, _
import tempfile
import binascii
import base64
import certifi
import urllib3
import pytz
import xlrd

_logger = logging.getLogger(__name__)


class SaleOrderManualImport(models.Model):
    """ model for adding the feature of import function of sale order"""
    _name = 'sale.order.manual.import'
    _description = "Sale order manual import"
    _order = 'id desc'
    _rec_name = 'rec_name'

    rec_name = fields.Char(string="Name", copy=False)
    description = fields.Char(string="Description", copy=False)
    upload_file = fields.Binary(string='Upload File', attachment=True)
    filename = fields.Char()
    rec_edit = fields.Html(sanitize=False, compute='_compute_rec_edit', store=False)
    file_name = fields.Char(string="File Name")
    currently_active = fields.Boolean(string='Currently Active')
    row_no = fields.Integer(string='Last Update Row Number SO')
    journal_row_no = fields.Integer(string='Last Update Row Number Journal')
    total_row_no = fields.Integer(string='Total Row Number', compute="get_sheet_total_row", store=True)
    sale_count = fields.Integer(string='Success', compute="get_so_count")
    failure_count = fields.Integer(string='Failed', compute="get_so_count")
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer')
    emp_id = fields.Many2one(comodel_name='hr.employee', string='Order Sales Person')
    product_id = fields.Many2one(comodel_name='product.product', string='Product')
    industry_id = fields.Many2one(comodel_name='res.partner.industry', string='Customer Industry')
    tax_id = fields.Many2one(comodel_name='account.tax', string='Tax')
    item_category_id = fields.Many2one(comodel_name='item.category', string='Item Category')
    region_id = fields.Many2one(comodel_name='sales.region', string='Region')
    limit = fields.Integer(string='Limit', default=300)
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('in_progress', 'In Progress'),
                                        ('complete_with_fail', 'Completed With Failures'),
                                        ('complete', 'Completed')
                                        ], default='draft', copy=False, string="Status")

    order_ids = fields.Many2many(comodel_name='sale.order', relation='import_saleorder_rel', column1='import_id',
                                 column2='order_id', string='Orders')
    line_ids = fields.One2many(comodel_name='sale.import.lines', inverse_name='so_import_id', string='Failures')
    start_time = fields.Datetime("Start Time")
    end_time = fields.Datetime("End Time")
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        sequence_code = 'sale.order.import.sequence'
        new_name = self.env['ir.sequence'].next_by_code(sequence_code) or '/'
        vals.update({'rec_name': new_name})
        return super(SaleOrderManualImport, self).create(vals)

    def get_so_count(self):
        for rec in self:
            rec.sale_count = len(rec.order_ids)
            rec.failure_count = len(rec.line_ids)

    def print_xlsx(self):
        data = {
            'ids': self.env.context.get('active_ids', []),
            'model': 'sale.order.manual.import',
        }
        report = self.env.ref('sale_extended.sales_import_xlsx')
        report.report_file = "Qwqer_Sale_Import - %s" % (self.rec_name or '')
        if self._context.get('download_failed_orders', False):
            report.report_file = "Qwqer_Sale_Import_Fail- %s" % (self.rec_name or '')
        return self.env.ref('sale_extended.sales_import_xlsx').report_action(self, data=data)

    @api.depends('upload_file')
    def get_sheet_total_row(self):
        for rec in self:
            if rec.upload_file:
                try:
                    file_string = tempfile.NamedTemporaryFile(suffix=".xlsx")
                    file_string.write(binascii.a2b_base64(self.upload_file))
                    book = xlrd.open_workbook(file_string.name)
                    sheet = book.sheet_by_index(0)
                except Exception as e:
                    raise UserError(_("Please choose xlsx file"))
                if sheet.row_values(0) != ['Sl No', 'Order Status', 'Payment Mode',
                                           'Service Order Date(2022-04-30 09:51:42)', 'Weight', 'Est. Time',
                                           'Est. Dst.', 'Order Amount', 'Amount', 'Discount', 'Pricing Plan',
                                           'Driver ID', 'To Name', 'To Phone No', 'To Address', 'Pickup Distance',
                                           'Deliver Distance', 'From Name', 'From Phone No', 'From Address',
                                           'Sender Locality', 'Order Source', 'Payment Status', 'Merchant Order ID',
                                           'Merchant Amount', 'Merchant Payment Mode', 'Quantity']:
                    raise UserError(_("File Template Mismatch"))
                if sheet.nrows > 0:
                    rec.total_row_no = sheet.nrows
                    if rec.total_row_no > 10000:
                        raise UserError(_("File Size is too Large Please Split File"))
                    if rec.total_row_no > 500:
                        rec.limit = 500
                    else:
                        rec.limit = rec.total_row_no
                    # if rec.total_row_no > 100:
                    #     rec.credit_journal_limit = 100
                    # else:
                    #     rec.credit_journal_limit = rec.total_row_no

    def import_so_file(self, limit=1):
        _logger.info("Sale order Import Function.**Time:%s", fields.datetime.now())
        active_datas = self.env['sale.order.manual.import'].sudo().search(
            [('state', 'not in', ('complete', 'complete_with_fail')),
             ('upload_file', '!=', False)], order='id asc', limit=limit or 1)
        for active_data in active_datas:
            if active_data:
                active_data.start_time = datetime.now()
                if active_data.total_row_no == active_data.row_no:
                    # active_data.action_send_mail()
                    if active_data.line_ids:
                        active_data.state = 'complete_with_fail'
                    else:
                        active_data.state = 'complete'
                    active_data.currently_active = False
                else:
                    try:
                        file_string = tempfile.NamedTemporaryFile(suffix=".xlsx")
                        file_string.write(binascii.a2b_base64(active_data.upload_file))
                        book = xlrd.open_workbook(file_string.name)
                        sheet = book.sheet_by_index(0)
                    except Exception:
                        _logger.info("Error Occur in Sale Order Import")
                    active_data.currently_active = True
                    active_data.state = 'in_progress'
                    active_data.so_creation(sheet)
                    active_data.end_time = datetime.now()

    def so_creation(self, sheet):
        if self.total_row_no != self.row_no:
            start_line = False
            start = self.row_no
            stop = self.row_no + self.limit
            if self.row_no == 0:
                start = 0
                start_line = True
            for row_line in range(start, stop):

                if self.row_no < self.total_row_no:
                    flag = False
                    if start_line:
                        start_line = False
                    else:
                        if sheet.row_values(row_line):
                            line = list(sheet.row_values(row_line))
                            if line[13] and isinstance(line[13], float):
                                line[13] = str(int(line[13]))

                            try:
                                state = 'sale'
                                payment_mode = False
                                order_status = False
                                merchant_payment_mode = False
                                date = False
                                driver_id = False
                                if not line[2]:
                                    msg = "Payment Mode Missing"
                                    self.create_sale_import_line(int(line[0]), msg)
                                    flag = True
                                if line[21] not in ['API', 'Admin', 'CSV', 'QSHOP', 'iOS', 'Shop', 'Web',
                                                    'Android']:
                                    msg = "Wrong Or Missing Order Source"
                                    self.create_sale_import_line(int(line[0]), msg)
                                    flag = True
                                if not line[22]:
                                    msg = "Payment Status Missing"
                                    self.create_sale_import_line(int(line[0]), msg)
                                    flag = True
                                else:
                                    if line[22] != 'Not Paid':
                                        msg = "Wrong Payment Status"
                                        self.create_sale_import_line(int(line[0]), msg)
                                        flag = True
                                if line[1]:
                                    order_status = self.env['order.status'].sudo().search([('name', '=', str(line[1]))],
                                                                                          limit=1)
                                    if order_status and order_status.is_cancel_order:
                                        state = 'cancel'
                                    else:
                                        if not line[11]:
                                            msg = "Driver ID Missing"
                                            self.create_sale_import_line(int(line[0]), msg)
                                            flag = True
                                        else:
                                            driver_id = self.env['hr.employee'].sudo().search([('driver_uid','=',str(int(line[11])))])
                                            if not driver_id:
                                                msg = "Wrong Driver ID"
                                                self.create_sale_import_line(int(line[0]), msg)
                                                flag = True
                                            else:
                                                if driver_id.region_id != self.region_id:
                                                    msg='Mismatch in driver region and sale order region'
                                                    self.create_sale_import_line(int(line[0]), msg)
                                                    flag = True

                                if line[3]:
                                    check_line_date = datetime.strptime(line[3], '%Y-%m-%d %H:%M:%S')
                                    dt_1 = self.utc_time_conv(str(line[3]))
                                    date = datetime.strptime(dt_1, '%Y-%m-%d %H:%M:%S')

                                    today = (datetime.now()).strftime('%Y-%m-%d 00:00:00')
                                    format_today = datetime.strptime(today, '%Y-%m-%d %H:%M:%S')
                                    check_date = (format_today - timedelta(days=30))
                                    check_end_date = (format_today + timedelta(days=5))


                                    if check_line_date < check_date:
                                        msg = "You can't create sale orders dated before 5 days from current date"
                                        self.create_sale_import_line(int(line[0]), msg)
                                        flag = True
                                    if check_line_date > check_end_date:
                                        msg = "You can't create sale orders dated After 5 days from current date"
                                        self.create_sale_import_line(int(line[0]), msg)
                                        flag = True

                                if not flag:
                                    if line[2]:
                                        payment_mode = self.env['payment.mode'].sudo().search(
                                            [('name', '=', str(line[2]))], limit=1)
                                    if line[25]:
                                        merchant_payment_mode = self.env['payment.mode'].sudo().search(
                                            [('name', '=', str(line[25]))], limit=1)
                                    if payment_mode and payment_mode.is_credit_payment:
                                        sequence_order_id = self.env['ir.sequence'].next_by_code(
                                            'delivery.order.id.sequence') or '/'
                                        so_data = {'state': 'draft',
                                                   'partner_id': self.partner_id.id,
                                                   'service_type_id':self.partner_id.service_type_id.id if self.partner_id.service_type_id else False ,
                                                   'order_sales_person': self.emp_id.id,
                                                   'region_id': self.region_id.id,
                                                   'payment_mode_id': payment_mode and payment_mode.id or False,
                                                   'order_id': sequence_order_id,
                                                   'order_status_id': order_status.id,
                                                   'order_date': date,
                                                   'weight': line[4],
                                                   'estimated_time': line[5],
                                                   'estimated_distance': line[6],
                                                   'order_amount': float(line[7]),
                                                   'total_amount': float(line[8]),
                                                   'discount_amount': float(line[9]),
                                                   'pricing_plan': str(line[10]),
                                                   'driver_id': driver_id and driver_id.id or False,
                                                   'driver_name': driver_id and driver_id.name or False,
                                                   'driver_phone': driver_id and driver_id.work_phone or False,
                                                   'to_name': str(line[12]),
                                                   'to_phone_no': line[13],
                                                   'to_address': line[14],
                                                   'pickup_distance': line[15],
                                                   'deliver_distance': line[16],
                                                   'item_type': self.item_category_id and self.item_category_id.name or '',
                                                   'description': self.item_category_id and self.item_category_id.name or '',
                                                   'from_name': line[17],
                                                   'from_phone_no': line[18],
                                                   'from_address': line[19],
                                                   'sender_locality': line[20],
                                                   'industry_id': self.industry_id.id,
                                                   'order_source': line[21],
                                                   'payment_status': line[22],
                                                   'is_credit_journal_created': False,
                                                   'merchant_order_id': line[23] or '',
                                                   'merchant_order_amount': line[24] and float(line[24]),
                                                   'merchant_payment_mode_id': merchant_payment_mode and merchant_payment_mode.id or False,
                                                   'from_sale_import': True,
                                                   'order_line': [(0, 0, {'product_id': self.product_id.id,
                                                                          'name': self.product_id.name,
                                                                          'tax_id': [(6, 0, self.tax_id.ids)],
                                                                          'product_uom_qty': line[26],
                                                                          'price_unit': line[8],
                                                                          })]
                                                   }
                                        so_id = self.env["sale.order"].create(so_data)
                                        so_id.onchange_driver_id()
                                        # so_id.onchange_partner_id()
                                        _logger.info("Sale order created for order id %s.**Time:%s", line[0],
                                                     fields.datetime.now())
                                        if state == 'cancel':
                                            _logger.info("Sale order Cancelled for order id %s.**Time:%s", line[0],
                                                         fields.datetime.now())
                                            so_id.action_cancel()
                                        else:
                                            _logger.info("Sale order Confirmed for order id %s.**Time:%s", line[0],
                                                         fields.datetime.now())
                                            so_id.action_confirm()
                                        if so_id.order_status_id:
                                            if so_id.merchant_order_amount > 0 and so_id.order_status_id.code == "4":
                                                if not so_id.is_merchant_journal:
                                                    _logger.info(
                                                        "Sale order Merchant Journal started for order id %s.**Time:%s",
                                                        line[0], fields.datetime.now())
                                                    # so_id.create_merchant_journal()
                                                    _logger.info(
                                                        "Sale order Merchant Journal created for order id %s.**Time:%s",
                                                        line[0], fields.datetime.now())

                                        self.order_ids = [(4, so_id.id)]
                                        _logger.info("Complete Sale order creation for order id %s.**Time:%s", line[0],
                                                     fields.datetime.now())
                                    else:
                                        if payment_mode and not payment_mode.is_credit_payment:
                                            msg = "Not Credit Payment Mode"
                                            self.create_sale_import_line(int(line[0]), msg)
                                            _logger.info(
                                                "Sale order creation Payment mode error for order id %s.**Time:%s",
                                                line[0], fields.datetime.now())
                                        else:
                                            msg = "Wrong Payment Mode"
                                            self.create_sale_import_line(int(line[0]), msg)

                                            _logger.info(
                                                "Sale order creation Payment mode missing error for order id %s.**Time:%s",
                                                line[0], fields.datetime.now())
                            except Exception as e:
                                msg="Error Occur in excel data"
                                self.create_sale_import_line(int(line[0]),msg)
                                _logger.info("Sale order creation error for order id %s.**Time:%s", line[0],
                                             fields.datetime.now())
                else:
                    break
                self.row_no += 1


    def action_view_sale_data(self):
        for rec in self:
            if rec.order_ids:
                return {
                    'name': _('Sale Orders'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'sale.order',
                    'domain': [('id', 'in', rec.order_ids.ids)]
                }

    @api.model
    def utc_time_conv(self, date):
        local = pytz.timezone(self.env.user.tz or 'UTC')
        # _logger.info("From date %s", start)
        from_naive_schedule = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        from_local_dt_schedule = local.localize(from_naive_schedule, is_dst=None)
        utc_from_date = from_local_dt_schedule.astimezone(pytz.utc)
        str_utc_from_dt = datetime.strftime(utc_from_date, "%Y-%m-%d %H:%M:%S")
        return str_utc_from_dt


    def create_sale_import_line(self,line,msg):
        if line and msg:
            self.env["sale.import.lines"].create({'name': line,
                                                  'state': 'fail',
                                                  'description':msg,
                                                  'so_import_id': self.id})
        return True

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            product = self.env.company.product_id
            rec.product_id = product.id or False
            if rec.partner_id:
                rec.tax_id = rec.partner_id.b2b_sale_order_tax_ids and rec.partner_id.b2b_sale_order_tax_ids[
                    0].id or False
                rec.region_id = rec.partner_id.region_id and rec.partner_id.region_id.id or False
                rec.emp_id = rec.partner_id.order_sales_person and rec.partner_id.order_sales_person.id or False
                rec.industry_id = rec.partner_id.industry_id and rec.partner_id.industry_id.id or False
                rec.item_category_id = rec.partner_id.item_category_id and rec.partner_id.item_category_id.id or False
            else:
                rec.tax_id = False
                rec.region_id = False
                rec.emp_id = False
                rec.industry_id = False
                rec.item_category_id = False
    def unlink(self):
        for rec in self:
            if not self.env.user.has_group('base.group_system'):
                if rec.state != 'draft':
                    raise Warning(_('Sorry!You cannot delete records not in draft state'))
            return super(SaleOrderManualImport, self).unlink()



class SaleImportLine(models.Model):
    _name = 'sale.import.lines'
    _description = 'Manual Sale Import Lines'
    _order = 'id asc'

    name = fields.Char(string="Sl No", copy=False)
    state = fields.Selection(selection=[
        ('success', 'Success'), ('fail', 'Failed')],
        string="Status")
    so_import_id = fields.Many2one('sale.order.manual.import')
    description = fields.Char(string="Description", copy=False)
