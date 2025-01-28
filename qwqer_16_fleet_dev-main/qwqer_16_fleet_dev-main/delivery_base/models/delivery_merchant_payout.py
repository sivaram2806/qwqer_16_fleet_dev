# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from psycopg2 import OperationalError
from cashfree_sdk.payouts import Payouts
from cashfree_sdk.payouts.beneficiary import Beneficiary
from cashfree_sdk.payouts.transfers import Transfers
from cashfree_sdk.exceptions.exceptions import BadRequestError, EntityDoesntExistError
import pytz
import itertools
import base64
import json
from dateutil import tz
import logging

_logger = logging.getLogger(__name__)


class MerchantPayout(models.Model):
    """This model delivery.merchant.payout is to make merchant payout  for delivery(qwqer express) merchant"""
    _name = 'delivery.merchant.payout'
    _description = 'Delivery Merchant Payout'
    _inherit = ['mail.thread']
    _rec_name = 'rec_name'
    _order = 'id desc'

    rec_name = fields.Char("Name")
    description = fields.Text("Description")
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('approve', 'Approved'),
        ('pending', 'Pending'),
        ('complete_with_fail', 'Completed With Failures'),
        ('complete', 'Completed'), ], string='Status', default='draft', track_visibility='onchange')
    approve_date = fields.Date("Approved On")
    line_count = fields.Integer(string="Payout Count", compute="get_payout_count", store=True)
    active = fields.Boolean(string='Active', default=True)
    cashfree_ref = fields.Char(string="Payment Gateway Ref#", copy=False)
    transfer_date = fields.Datetime(string="Transaction Date", track_visibility='onchange', copy=False)
    processed_date = fields.Datetime(string="Processed Date", track_visibility='onchange', copy=False)
    total_amount = fields.Float(string='Total Amount', compute="get_total_amount", store=True, digits='Product Price')
    invoice_created = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Invoice Created', compute="update_invoice_created", store=True)
    region_id = fields.Many2one('sales.region')
    approved_user_id = fields.Many2one(comodel_name='res.users', string='Approved By')
    line_ids = fields.One2many(comodel_name='delivery.merchant.payout.lines', inverse_name='payout_id',
                               string='Merchant Payouts')
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        company_id = self.env.company.id
        sequence = self.env['ir.sequence'].search(
            [('company_id', '=', company_id), ('code', '=', 'delivery.merchant.payout.seq')])
        if not sequence:
            sequence = self.env['ir.sequence'].search([('code', '=', 'delivery.merchant.payout.seq')], limit=1)
            new_sequence = sequence.sudo().copy()
            new_sequence.company_id = company_id
            vals['rec_name'] = new_sequence.next_by_id()
        else:
            vals['rec_name'] = self.env['ir.sequence'].next_by_code('delivery.merchant.payout.seq')
        return super(MerchantPayout, self).create(vals)

    def action_archive(self):
        archive_flag = True
        if len(self) > 1:
            recs = self.filtered(lambda r: r.state in ('approve', 'pending', 'complete_with_fail', 'complete'))
            if recs:
                archive_flag = False
        else:
            if self.state in ('approve', 'pending', 'complete_with_fail', 'complete'):
                archive_flag = False
        if archive_flag:
            return super(MerchantPayout, self).action_archive()
        else:
            raise ValidationError(_('You can archive only draft payouts'))

    def unlink(self):
        unlink_flag = True
        if len(self) > 1:
            recs = self.filtered(lambda r: r.state in ('approve', 'pending', 'complete_with_fail', 'complete'))
            if recs:
                unlink_flag = False
        else:
            if self.state in ('approve', 'pending', 'complete_with_fail', 'complete'):
                unlink_flag = False
        if unlink_flag:
            return super(MerchantPayout, self).unlink()
        else:
            raise ValidationError(_('You can delete only draft payouts'))

    @api.depends('line_ids')
    def get_payout_count(self):
        for rec in self:
            if rec.line_ids:
                rec.line_count = len(rec.line_ids)

    @api.depends('line_ids')
    def get_total_amount(self):
        """compute the total amount to pay before taxes, service charges and other deduction displayed in tree view"""
        for rec in self:
            total = 0.0
            for line in rec.line_ids:
                total += line.final_pay
            rec.total_amount = total

    @api.depends('state', 'line_ids.invoice_id')
    def update_invoice_created(self):
        """compute the line invoice status"""
        for rec in self:
            invoice_create = True
            rec.invoice_created = 'no'
            if rec.state in ('complete_with_fail', 'complete') and rec.line_ids:
                for line in rec.line_ids:
                    if line.payment_state == 'success' and not line.invoice_id and line.service_charge != 0.00:
                        invoice_create = False
                        break
                if invoice_create:
                    rec.invoice_created = 'yes'
                else:
                    rec.invoice_created = 'no'

    def action_update_lines(self):
        """function to add or update payout line"""
        for rec in self:
            if rec.state == 'draft':
                local = pytz.timezone(self.env.user.tz or pytz.utc)
                if rec.line_ids:
                    for line in rec.line_ids:
                        if line.line_ids:
                            if len(line.line_ids) > 1:
                                query1 = (
                                        """UPDATE account_move_line SET merchant_payout_id = Null WHERE id in %s;""" % str(
                                    tuple(line.line_ids.ids)))
                            else:
                                query1 = (
                                        """UPDATE account_move_line SET merchant_payout_id = Null WHERE id = %d;""" % line.line_ids.id)
                            self.env.cr.execute(query1)
                rec.line_ids = False
                rec.create_payout_lines()
                if rec.line_ids:
                    rec.line_ids.onchange_service_chrg()
                    rec.line_ids.onchange_taxes()
            else:
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('%s fetch customers is restricted.Payout is already in %s status.Please Refresh!' % (
                    rec.name, state)))

    def create_payout_lines(self):
        """function to create payout lines"""
        for rec in self:
            if rec.to_date and rec.region_id:
                so_data = rec.get_so_data()
                if so_data:
                    for partner_id, order_ids in so_data.items():
                        query = self.env['account.move.line']._where_calc([
                            ('full_reconcile_id', '=', False),
                            ('merchant_payout_id', '=', False),
                            ('balance', '!=', 0),
                            ('account_id.reconcile', '=', True),
                            ('merchant_order_id', 'in', order_ids),
                            ('credit', '>', 0.0),
                            ('partner_id', '=', partner_id),
                            ('service_type_id.is_delivery_service', '=', True)
                        ])
                        from_clause, where_clause, where_clause_params = query.get_sql()
                        sql = """
                        SELECT account_move_line.id as move_line_ids FROM %(from)s WHERE %(where)s 
                        """ % {'from': from_clause, 'where': where_clause}
                        self.env.cr.execute(sql, where_clause_params)
                        move_lines = list(itertools.chain(*self.env.cr.fetchall()))
                        if move_lines:
                            payout_line_id = self.env['delivery.merchant.payout.lines'].sudo().create(
                                {'to_date': rec.to_date,
                                 'from_date': rec.from_date,
                                 'customer_id': partner_id,
                                 'payout_id': rec.id,
                                 'line_ids': move_lines})
                            payout_line_id.line_ids.write(({
                                'merchant_payout_id': rec.id,
                            }))
                if not so_data or not move_lines:
                    rec.line_ids = False

    def get_so_data(self):
        """function to get sale order data to calculate payout lines"""
        for rec in self:
            if self.to_date and self.region_id:
                dict = {}
                local_tz = pytz.timezone(self.env.user.tz or 'UTC')
                # Convert from_date and to_date to UTC
                from_date_str = f"{self.from_date:%Y-%m-%d} 00:00:00"
                to_date_str = f"{self.to_date:%Y-%m-%d} 23:59:59"
                utc_from_date = local_tz.localize(datetime.strptime(from_date_str, "%Y-%m-%d %H:%M:%S")).astimezone(
                    pytz.utc)
                utc_to_date = local_tz.localize(datetime.strptime(to_date_str, "%Y-%m-%d %H:%M:%S")).astimezone(
                    pytz.utc)

                merchant_query = self.env['sale.order']._where_calc([
                    ('create_date', '>=', utc_from_date),
                    ('create_date', '<=', utc_to_date),
                    ('state', '=', 'sale'),
                    ('merchant_order_amount', '>', 0.0),
                    ('merchant_journal_ids', '=', False),
                    ('order_status_id.code', '=', '4'),
                    ('partner_id.region_id', '=', self.region_id.id),
                    ('partner_id.service_type_id.is_delivery_service', '=', True),
                    ('service_type_id.is_delivery_service', '=', True)
                ])
                from_clause, where_clause, where_clause_params = merchant_query.get_sql()

                merchant_sql = """
                   SELECT sale_order.order_id as so_id FROM %(from)s WHERE %(where)s 
                   """ % {'from': from_clause, 'where': where_clause}

                self.env.cr.execute(merchant_sql, where_clause_params)
                no_merchant_res = list(itertools.chain(*self.env.cr.fetchall()))

                if no_merchant_res:
                    raise ValidationError(
                        _("Merchant journal is not created for the sale orders %s" % (no_merchant_res)))
                else:
                    query = self.env['sale.order']._where_calc([
                        ('create_date', '>=', utc_from_date),
                        ('create_date', '<=', utc_to_date),
                        ('state', '=', 'sale'),
                        ('merchant_journal_ids', '!=', False),
                        ('partner_id.region_id', '=', self.region_id.id),
                        ('partner_id.service_type_id.is_delivery_service', '=', True),
                        ('service_type_id.is_delivery_service', '=', True),
                        ('company_id', '=', self.env.company.id)
                    ])
                    from_clause, where_clause, where_clause_params = query.get_sql()
                    sql = """
                       SELECT sale_order.id as so_id,sale_order.partner_id as cust_id FROM %(from)s WHERE %(where)s 
                       """ % {'from': from_clause, 'where': where_clause}
                    self.env.cr.execute(sql, where_clause_params)
                    res = self.env.cr.dictfetchall()
                    for data in res:
                        if data['cust_id'] not in dict:
                            dict.update({data.get('cust_id'): [data.get('so_id')]})
                        else:
                            dict[data['cust_id']].extend([data.get('so_id')])
                return dict

    def action_recompute_lines(self):
        """function to recompute the calculation on the payout lines"""
        for rec in self:
            if rec.state == 'draft':
                for line in rec.line_ids:

                    local_tz = pytz.timezone(self.env.user.tz or 'UTC')
                    # Convert from_date and to_date to UTC
                    from_date_str = f"{self.from_date:%Y-%m-%d} 00:00:00"
                    to_date_str = f"{self.to_date:%Y-%m-%d} 23:59:59"
                    utc_from_date = local_tz.localize(datetime.strptime(from_date_str, "%Y-%m-%d %H:%M:%S")).astimezone(
                        pytz.utc)
                    utc_to_date = local_tz.localize(datetime.strptime(to_date_str, "%Y-%m-%d %H:%M:%S")).astimezone(
                        pytz.utc)

                    query = self.env['sale.order']._where_calc([
                        ('create_date', '>=', utc_from_date),
                        ('create_date', '<=', utc_to_date),
                        ('state', '=', 'sale'),
                        ('merchant_journal_ids', '!=', False),
                        ('partner_id.region_id', '=', self.region_id.id),
                        ('partner_id', '=', line.customer_id.id),
                        ('partner_id.service_type_id.is_delivery_service', '=', True),
                        ('service_type_id.is_delivery_service', '=', True)
                    ])
                    from_clause, where_clause, where_clause_params = query.get_sql()
                    sql = """
                    SELECT sale_order.id FROM %(from)s WHERE %(where)s 
                    """ % {'from': from_clause, 'where': where_clause}
                    self.env.cr.execute(sql, where_clause_params)
                    so_data = list(itertools.chain(*self.env.cr.fetchall()))
                    if so_data:
                        query = self.env['account.move.line']._where_calc([
                            ('full_reconcile_id', '=', False),
                            ('merchant_payout_id', '=', rec.id),
                            ('balance', '!=', 0),
                            ('account_id.reconcile', '=', True),
                            ('merchant_order_id', 'in', so_data),
                            ('credit', '>', 0.0),
                            ('partner_id', '=', line.customer_id.id),
                            ('service_type_id.is_delivery_service', '=', True)
                        ])
                        from_clause, where_clause, where_clause_params = query.get_sql()
                        sql = """
                        SELECT account_move_line.id as move_line_ids FROM %(from)s WHERE %(where)s 
                        """ % {'from': from_clause, 'where': where_clause}
                        self.env.cr.execute(sql, where_clause_params)
                        move_lines = list(itertools.chain(*self.env.cr.fetchall()))
                        if move_lines:
                            line.line_ids = [(6, 0, move_lines)]
                            line.line_ids.write(({
                                'merchant_payout_id': rec.id,
                            }))
                    if not so_data or not move_lines:
                        line.unlink()
                    line.onchange_service_chrg()
                    line.onchange_taxes()
            else:
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('%s recompute lines is restricted.Payout is already in %s status.Please Refresh!' % (
                    rec.name, state)))

    def action_approve(self):
        """function to approve the payout and save the approved user"""
        for rec in self:
            if rec.state == 'draft':
                for line in rec.line_ids:
                    if line.final_pay < 0.0:
                        raise UserError(_('Transfer ID %s Total Payout is Negative' % (line.transfer_ref)))
                    elif line.final_pay > 0.00 and line.final_pay < 1.00:
                        raise UserError(_('Transfer ID %s Total Payout value can be 0 or greater than or equal to 1' % (
                            line.transfer_ref)))
                rec.write({'approved_user_id': self.env.user.id, 'approve_date': datetime.today(), 'state': "approve"})
            else:
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(
                    _('%s approved is restricted.Payout is already in %s status.Please Refresh!' % (rec.name, state)))

    def set_to_draft(self):
        """function to change the sate to draft"""
        for rec in self:
            if rec.state == 'approve':
                rec.state = "draft"
            else:
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('%s set to draft is restricted.Payout is already in %s status.Please Refresh!' % (
                    rec.name, state)))

    def init_cashfree(self):
        """function to init the cashfree before making cashfree requests"""
        cashfree_id = self.env['cash.free.credentials'].sudo().search([("company_id", "=", self.company_id.id)],
                                                                      limit=1)
        if not cashfree_id:
            raise UserError("Cashfree configuration is missing, Please contact System Administrator")
        app_id, app_key = cashfree_id.payout_app_id, cashfree_id.payout_key
        env = self.env.company.cashfree_env
        Payouts.init(app_id, app_key, env, public_key=base64.b64decode(cashfree_id.public_key).decode('utf-8'))

    def get_benef_details(self, cus_id):
        """function to get and validate partner(merchant) beneficiary details with cashfree """
        for rec in self:
            self.init_cashfree()
            try:
                bene_details = Beneficiary.get_bene_details(cus_id.beneficiary)
                json_data = json.loads(bene_details.content)
                if 'status' in json_data and json_data['status'] == 'SUCCESS':
                    return
                else:
                    message = "%s Beneficiary[%s] Invalid" % (cus_id.name, cus_id.beneficiary)
                    raise ValidationError(_(message))
            except Exception as e:
                message = "%s Beneficiary[%s] does not exist" % (cus_id.name, cus_id.beneficiary)
                raise ValidationError(_(message))

    def check_state(self):
        for rec in self:
            if rec.line_ids:
                # Update zero final pay records to 'success' state
                zero_values = rec.line_ids.filtered(lambda line: line.final_pay == 0.00)
                zero_values.write({'payment_state': "success"})

                non_success_lines = rec.line_ids.filtered(lambda line: line.payment_state != 'success')
                if non_success_lines:
                    # Check for any 'pending' or 'initiate' states within non-success lines
                    if any(line.payment_state in ('pending', 'initiate') for line in non_success_lines):
                        rec.state = 'pending'
                    else:
                        rec.state = 'complete_with_fail'
                else:
                    rec.state = 'complete'

    def action_batch_payment(self):
        for rec in self:
            try:
                query = "SELECT id FROM delivery_merchant_payout WHERE id = %s FOR UPDATE NOWAIT"
                self.env.cr.execute(query, (rec.id,))
            except OperationalError:
                raise UserError(
                    _('This record is currently being processed in another session. Please try again later.'))
            if rec.state == 'approve':
                entries = []
                non_benf_list = []
                if rec.line_ids:
                    _logger.info("Beneficiary checking started in merchant payout******************%s", rec.rec_name)
                    for line in rec.line_ids:
                        if line.final_pay >= 1.0:
                            if line.customer_id.beneficiary:
                                self.get_benef_details(line.customer_id)
                                vals = {}
                                vals.update({
                                    "transferId": line.transfer_ref,
                                    "transferMode": "banktransfer",
                                    "beneId": line.customer_id.beneficiary or '',
                                    "amount": line.final_pay,

                                })
                                entries.append(vals)
                            else:
                                non_benf_list.append(line.customer_id.name)
                    _logger.info("Beneficiary checking ended in merchant payout******************%s", rec.rec_name)
                    if non_benf_list:
                        cus_names = ', '.join(non_benf_list)
                        raise UserError(_('Customers [%s] have no Beneficiary In Cashfree' % (cus_names)))
                    else:
                        batch_payment_res = rec.cash_free_batch_transfer(entries)
                        _logger.info(
                            "%s Merchant Payout Created **********************: %s" % (rec.rec_name, batch_payment_res))

                        if batch_payment_res['status'] == 'SUCCESS':
                            rec.transfer_date = fields.datetime.now()
                            if batch_payment_res['data']['referenceId']:
                                rec.cashfree_ref = batch_payment_res['data']['referenceId']
                            else:
                                rec.cashfree_ref = ''
                        elif batch_payment_res['status'] == 'PENDING':
                            rec.transfer_date = fields.datetime.now()
                        else:
                            raise ValidationError(_("Batch Transfer Failed\nError:%s", batch_payment_res))

                        if rec.line_ids:
                            rec.line_ids.write({'payment_state': 'initiate'})
                        rec.check_state()
            else:
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('%s batch payment is restricted.Payout is already in %s status.Please Refresh!' % (
                    rec.name, state)))

    def cash_free_batch_transfer(self, entries):
        self.init_cashfree()
        try:
            if entries:
                batch_tnx_create = Transfers.create_batch_transfer(batchTransferId=self.rec_name,
                                                                   batchFormat="BENEFICIARY_ID",
                                                                   batch=entries, deleteBene=1)
                response = json.loads(batch_tnx_create.content)
                return response
        except Exception as e:
            error_string = repr(e)
            message = "Batch Transfer Failed\nError:%s" % error_string
            raise ValidationError(_(message))

    def create_trns_journal_entry(self):
        for rec in self:
            delivery_service_type = self.env['partner.service.type'].search(
                [('is_delivery_service', '=', True), ("company_id", "=", self.company_id.id)], limit=1)
            accounts_data = self.env['merchant.payout.account.config'].sudo().search(
                [("company_id", "=", self.company_id.id)], limit=1)
            if rec.line_ids and accounts_data:
                for line in rec.line_ids:
                    move_line_list = []
                    account_id = line.line_ids[0].account_id
                    if line.payment_state == 'success' and not line.payment_journal_id:
                        if line.final_pay >= 1.0 or line.balance_amt + line.taxes + line.service_charge > 0:
                            move_line = {'account_id': account_id.id or False,
                                         'analytic_distribution': {
                                                                      line.customer_id.region_id and line.customer_id.region_id.analytic_account_id and line.customer_id.region_id.analytic_account_id.id: 100} or False,
                                         'debit': line.total_pay,
                                         'credit': 0.0,
                                         'name': 'Merchant Amount',
                                         'partner_id': line.customer_id.id or False,
                                         'service_type_id': delivery_service_type.id,
                                         }
                            move_line_list.append((0, 0, move_line))
                        if accounts_data.delivery_debit_transfer_account_id:
                            if line.balance_amt > 0:
                                move_line_2 = {
                                    'account_id': accounts_data.delivery_debit_transfer_account_id.id or False,
                                    'debit': 0.0,
                                    'credit': line.balance_amt,
                                    'analytic_distribution': {rec.region_id.analytic_account_id.id: 100} or False,
                                    'name': 'Merchant Amount-Deduction',
                                    'partner_id': line.customer_id.id or False,
                                    'service_type_id': delivery_service_type.id,
                                }

                                move_line_list.append((0, 0, move_line_2))
                            if line.taxes + line.service_charge > 0:
                                move_line_3 = {
                                    'account_id': accounts_data.delivery_debit_transfer_account_id.id or False,
                                    'debit': 0.0,
                                    'credit': line.taxes + line.service_charge,
                                    'analytic_distribution': {rec.region_id.analytic_account_id.id: 100} or False,
                                    'name': 'Merchant Amount-Service Charge',
                                    'partner_id': line.customer_id.id or False,
                                    'service_type_id': delivery_service_type.id,
                                }

                                move_line_list.append((0, 0, move_line_3))
                        if line.final_pay >= 1:
                            move_line_1 = {'account_id': accounts_data.delivery_credit_transfer_account_id.id or False,
                                           'debit': 0.0,
                                           'name': 'Merchant Amount',
                                           'credit': line.final_pay,
                                           'service_type_id': delivery_service_type.id,
                                           }

                            move_line_list.append((0, 0, move_line_1))

                        vals = {
                            'ref': rec.rec_name or '',
                            'line_ids': move_line_list,
                            'move_type': 'entry',
                            'service_type_id': delivery_service_type.id,
                            'region_id': line.customer_id.region_id and line.customer_id.region_id.id or False,
                            'journal_id': accounts_data.delivery_transfer_journal_id and accounts_data.delivery_transfer_journal_id.id or False, }

                        move_id = self.env['account.move'].sudo().create(vals)
                        move_id.action_post()
                        line.payment_journal_id = move_id.id
                        for trans_line in line.line_ids:
                            trans_line.merchant_payout_id = rec.id
                    mv_list = line.line_ids.ids or []
                    is_recon_list = line.line_ids.mapped('full_reconcile_id') or []
                    if mv_list and not is_recon_list:
                        for mv_line in line.payment_journal_id.line_ids:
                            if mv_line.debit > 0.0:
                                mv_list.append(mv_line.id)
                        move_line_ids = self.env['account.move.line'].browse(mv_list)
                        move_line_ids.reconcile()

    def get_start_and_end(self, date):
        if date:
            time_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            tz_time = ''
            tz_name = self._context.get('tz', False) \
                      or self.env.user.tz
            if not tz_name:
                raise UserError(_('Please configure your time zone in Preferance'))
            if tz_name and time_obj:
                new_time = time_obj.replace(tzinfo=pytz.timezone('UTC')).astimezone(pytz.timezone(tz_name))
                est = tz.gettz(tz_name)
                today = new_time.date()
                start = datetime(today.year, today.month, today.day, tzinfo=tz.tzutc()).astimezone(est)
                end = start + timedelta(1)

                return start, end

    @api.model
    def to_utc_datetime(self, datetime_str):
        """Returns the given timestamp converted to the utc's timezone. Used while importing records

        :param datetime_str string: datetime value to be converted to the utc timezone
        :rtype: string
        :return: datetime string converted to timezone-aware datetime in utc
        timezone
        """
        if datetime_str:
            tz_name = self.env.user.tz or self._context.get('tz') or 'UTC'
            local = pytz.timezone(tz_name)
            local_dt = local.localize(fields.Datetime.from_string(datetime_str), is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            return fields.Datetime.to_string(utc_dt)

    @api.model
    def daily_payout_status(self):
        # This method is called by a cron task
        today = date.today()
        new_date = today + timedelta(days=-8)
        start, end = self.get_start_and_end(new_date.strftime("%Y-%m-%d %H:%M:%S"))
        utc_date_from = self.to_utc_datetime(end.strftime("%Y-%m-%d %H:%M:%S"))
        payout_ids = self.sudo().search([('transfer_date', '>=', utc_date_from)])
        for line in payout_ids:
            try:
                with self.env.cr.savepoint():
                    line.action_check_status()
            except Exception as e:
                pass

    def action_check_status(self):
        for rec in self:
            if rec.state in ('pending', 'complete_with_fail', 'complete'):
                if not rec.transfer_date:
                    rec.check_state()
                else:
                    try:
                        for line in rec.line_ids:
                            if line.final_pay >= 1.0:
                                _logger.info("start status update in merchant payout******************%s",
                                             line.transfer_ref)
                                rec.get_line_status(line.transfer_ref, line)
                                _logger.info("end status update in merchant payout******************%s",
                                             line.transfer_ref)
                        rec.create_trns_journal_entry()
                        rec.check_state()
                    except Exception as e:
                        error_string = repr(e)
                        message = "Batch Transfer Status Update  Failed\nError:%s" % error_string
                        raise ValidationError(_(message))
            else:
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('%s update status is restricted.Payout is already in %s status.Please Refresh!' % (
                    rec.name, state)))

    def get_line_status(self, transfer_id, line_id):

        def cancel_transactions(line):
            """Helper to cancel related journal entries, invoices, and payments for the line."""
            if line.payment_journal_id:
                line.unrec_entries()
            if line.invoice_id:
                line.invoice_id.button_draft()
                line.invoice_id.button_cancel()
            if line.payment_id:
                line.payment_id.action_draft()
                line.payment_id.cancel()

        def reset_line_entries(line):
            """Helper to reset line entries when not reinitiated."""
            if line.re_initiated != "yes":
                line.re_initiated = "no"
                if line.line_ids:
                    line.line_ids.write({'merchant_payout_id': False})

        for rec in self:
            if transfer_id and line_id:
                self.init_cashfree()
                try:
                    vals = None
                    get_transfer_status_response = Transfers.get_transfer_status(transferId=transfer_id)
                    json_data = json.loads(get_transfer_status_response.text)
                    transfer_data = json_data.get('data').get('transfer')

                    status = transfer_data.get('status')
                    processed_date = self.to_utc_datetime(transfer_data.get('processedOn')) or False
                    transfer_date = self.to_utc_datetime(transfer_data.get('addedOn')) or False
                    cashfree_ref = transfer_data.get('referenceId')
                    utr_ref = transfer_data.get('utr')
                    status_description = transfer_data.get('statusDescription')

                    if status == 'SUCCESS':
                        vals = {'payment_state': "success", 'processed_date': processed_date or transfer_date,
                                'transfer_date': transfer_date, 'cashfree_ref': cashfree_ref, 'utr_ref': utr_ref,
                                'status_description': status_description}
                    elif status in ('PENDING', 'PROCESSING'):
                        vals = {'payment_state': "pending", 'transfer_date': transfer_date,
                                'cashfree_ref': cashfree_ref, 'status_description': status_description}
                        cancel_transactions(line_id)
                    elif status == 'REVERSED':
                        vals = {'payment_state': "fail", 'processed_date': processed_date,
                                'transfer_date': transfer_date, 'cashfree_ref': cashfree_ref,
                                'status_description': status_description}
                        cancel_transactions(line_id)
                        reset_line_entries(line_id)
                    else:
                        vals = {'payment_state': "fail", 'processed_date': processed_date,
                                'transfer_date': transfer_date, 'cashfree_ref': cashfree_ref,
                                'status_description': status_description}
                        cancel_transactions(line_id)
                        reset_line_entries(line_id)

                    if vals:
                        line_id.write(vals)

                except Exception as e:
                    raise ValidationError(_("Line Status Update Failed\nError: %s") % str(e))

    def action_generate_invoice_lines(self):
        for rec in self:
            if rec.state not in ('complete_with_fail', 'complete'):
                state_label = dict(rec._fields['state'].selection).get(rec.state, '')
                raise UserError(_(
                    f"{rec.name} invoice generation is restricted. Payout is already in {state_label} status. Please refresh!"
                ))

            now = datetime.now()
            date = now.strftime("%Y-%m-%d %H:%M:%S")
            local = pytz.timezone(self.env.user.tz or pytz.utc)
            naive_dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            local_dt = local.localize(naive_dt, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            config = self.env['merchant.payout.account.config'].sudo().search(
                [("company_id", "=", self.company_id.id)], limit=1)
            if not config:
                raise UserError(_("Payout account configuration not found for the company."))
            product = rec.env.company.product_id
            accounts = product.get_product_accounts(fiscal_pos=False)
            payment_mode = self.env['payment.mode'].search([('is_credit_payment', '=', True)], limit=1)
            state_journal = self.env['state.journal'].search([('state_id', '=', rec.region_id.state_id.id)], limit=1)
            delivery_service_type = self.env['partner.service.type'].search(
                [('is_delivery_service', '=', True), ("company_id", "=", self.company_id.id)], limit=1)

            if not state_journal:
                raise UserError(_("State journal not found for the region."))
            lines = rec.line_ids.filtered(
                lambda l: not l.invoice_id and l.service_charge != 0 and l.payment_state == 'success')
            if not lines:
                raise ValidationError(_("Nothing to invoice"))
            for line in lines:
                invoice_line_vals = {
                    'product_id': product.id,
                    'account_id': accounts['income'].id,
                    'name': f"Cash collection charges from {rec.from_date} to {rec.to_date}.",
                    'analytic_distribution': {rec.region_id.analytic_account_id.id: 100},
                    'quantity': 1,
                    'price_unit': line.service_charge,
                    'tax_ids': [(6, 0, line.customer_id.b2b_invoice_tax_ids.ids)],
                    'service_type_id': delivery_service_type.id,
                }

                line_invoice = {'move_type': 'out_invoice',
                                'partner_id': line.customer_id.id,
                                'invoice_date': utc_dt.date(),
                                'journal_id': state_journal.delivery_journal_id.id,
                                'ref': rec.rec_name,
                                'service_type_id': delivery_service_type.id,
                                'region_id': rec.region_id.id,
                                'payment_mode_id': payment_mode and payment_mode.id or False,
                                'invoice_line_ids': [(0, 0, invoice_line_vals)],
                                }
                account_move = self.env["account.move"].create(line_invoice)
                account_move.sudo().action_post()
                line.invoice_id = account_move.id
