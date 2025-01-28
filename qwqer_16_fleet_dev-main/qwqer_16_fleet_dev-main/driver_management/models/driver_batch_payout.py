import pytz
import json
import base64
import logging

from datetime import datetime, timedelta, date

from odoo import api, fields, models, _
from collections import defaultdict
from cashfree_sdk.payouts import Payouts
from cashfree_sdk.payouts.beneficiary import Beneficiary
from dateutil.relativedelta import relativedelta
from cashfree_sdk.payouts.transfers import Transfers
from psycopg2 import OperationalError
from odoo.exceptions import Warning, UserError, RedirectWarning, ValidationError
from lxml import etree
from dateutil import tz

from ..models.driver_payout import STATUS

_logger = logging.getLogger(__name__)

PAYMENT_STATUS = [
    ('initiate', 'Initiated'),
    ('pending', 'Pending'),
    ('fail', 'Failed'),
    ('success', 'Success'), ]


class DriverBatchPayout(models.Model):
    _name = 'driver.batch.payout'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(DriverBatchPayout, self).get_view(view_id=view_id, view_type=view_type, **options)

        doc = etree.XML(res['arch'])
        if view_type == 'form' or view_type == "tree":
            if not self.env.user.has_group('base.group_system'):
                if not self.env.user.has_group(
                        'driver_management.group_approve_payout') and not self.env.user.has_group(
                        'driver_management.group_verify_payout'):
                    for node_form in doc.xpath("//form"):
                        node_form.set("edit", 'false')
                    for node_form in doc.xpath("//form"):
                        node_form.set("create", 'false')
                    for node_form in doc.xpath("//tree"):
                        node_form.set("create", 'false')
                    for node_form in doc.xpath("//form"):
                        node_form.set("delete", 'false')
                    for node_form in doc.xpath("//tree"):
                        node_form.set("delete", 'false')
        res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def _get_vendor(self):
        vendor_list = []
        if self.env.context.get('default_is_vendor_payout', False):
            employees = self.env['hr.employee'].search(
                [('driver_uid', '!=', False), ('is_under_vendor', '=', True), ('cashfree_payment', '=', False)])
            for employee in employees:
                vendor_list.append(employee.driver_partner_id.id)
        return [('id', 'in', vendor_list)]

    name = fields.Char("Name")
    description = fields.Text("Description", required=True)
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    state = fields.Selection(STATUS, string='Status', default='draft', tracking=True) #V13_field : state
    region_id = fields.Many2one('sales.region', string="Region", domain="[('company_id','=',company_id)]")
    user_id = fields.Many2one('res.users', string='User ID', copy=False)
    cashfree_ref = fields.Char(string="Payment Gateway Ref#", copy=False)
    transaction_date = fields.Datetime("Transaction Date", tracking=True,copy=False) #V13_field : transfer_date
    processed_date = fields.Datetime("Processed Date", tracking=True)
    total_amount = fields.Float(string='Total Amount', store=True, compute="get_total_amount",digits='Product Price')
    batch_payout_line_ids = fields.One2many('driver.batch.payout.lines', 'batch_payout_id', 'Employee Payouts') #V13_field : line_ids
    is_vendor_payout = fields.Boolean(string='Vendor Payout') #V13_field : vendor_payout_bool
    partner_id = fields.Many2one('res.partner', string='Vendor', domain=_get_vendor)
    bill_ids = fields.Many2many('account.move',string="Bill References", copy=False)
    line_count = fields.Integer(string="Payout Count", compute="get_payout_count",store=True)
    bill_count = fields.Integer(string='Bill Count', compute='_compute_bill_count')
    active = fields.Boolean('Active', default=True)
    is_reject = fields.Boolean('Is Reject', copy=False)
    deduction_entry_id = fields.Many2one('account.move', string="Deduction Entry", tracking=True,
                                         copy=False)
    is_cron_created = fields.Boolean('Is Cron Created', copy=False) #V13_field : automated_created
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    @api.model
    def create(self,vals):
        company_id = self.env.company.id
        sequence = self.env['ir.sequence'].search(
            [('company_id', '=', company_id), ('code', '=', 'payout.sequence')])
        if not sequence:
            sequence = self.env['ir.sequence'].search([('code', '=', 'payout.sequence')], limit=1)
            new_sequence = sequence.sudo().sudo().copy()
            new_sequence.company_id = company_id
            vals['name'] = self.env['ir.sequence'].next_by_code('payout.sequence') or '/'
        else:
            vals['name'] = self.env['ir.sequence'].with_company(company_id).next_by_code('payout.sequence') or '/'
        res = super().create(vals)
        self.validation_checks(res)
        return res

    def write(self,vals):
        res=super().write(vals)
        for rec in self:
            self.validation_checks(rec)
            if vals.get('region_id'):
                if rec.region_id and rec.batch_payout_line_ids and vals.get('region_id') != rec.batch_payout_line_ids.employee_id.region_id.id:
                    raise ValidationError('Allowed drivers from the selected region only.')
                else:
                    rec.action_recompute_lines()
        return res

    def unlink(self):
        # Define states that prevent deletion
        allowed_states = ('draft', 'cancel')
        # Check if any records have restricted states
        restricted_recs = self.filtered(lambda r: r.state not in allowed_states)
        if restricted_recs:
            raise ValidationError(_('You can delete only draft or cancelled payouts'))
        return super().unlink()

    @api.model
    def convert_to_utc(self, start, end):  # V13_method: utc_time_conv
        """
        Converts start and end datetime strings from user's local timezone to UTC.

        Args:
            start (str): Start datetime string in the format "%Y-%m-%d %H:%M:%S".
            end (str): End datetime string in the format "%Y-%m-%d %H:%M:%S".

        Returns:
            tuple: A tuple containing UTC start and end datetime strings in the same format.
        """
        # Determine the user's timezone or default to UTC
        user_timezone = pytz.timezone(self.env.user.tz or 'UTC')

        # Convert 'start' to UTC
        start_local_dt = user_timezone.localize(datetime.strptime(start, "%Y-%m-%d %H:%M:%S"), is_dst=None)
        start_utc = start_local_dt.astimezone(pytz.utc)
        str_utc_start = start_utc.strftime("%Y-%m-%d %H:%M:%S")

        # Convert 'end' to UTC
        end_local_dt = user_timezone.localize(datetime.strptime(end, "%Y-%m-%d %H:%M:%S"), is_dst=None)
        end_utc = end_local_dt.astimezone(pytz.utc)
        str_utc_end = end_utc.strftime("%Y-%m-%d %H:%M:%S")

        # Return the converted datetime strings
        return str_utc_start, str_utc_end

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

    def action_archive(self):
        restricted_states = ('draft', 'cancel')
        restricted_recs = self.filtered(lambda r: r.state in restricted_states)
        if restricted_recs:
            return super().action_archive()
        else:
            raise ValidationError(_('You can archive only draft/cancel payouts'))

    def validation_checks(self,record):
        if self.env.context.get('from_payout_form', False):
            no_driver_lines = record.batch_payout_line_ids.filtered(lambda x: not x.employee_id)
            if no_driver_lines:
                raise ValidationError(_("Driver Missing in Payout Lines"))
            for rec in record:
                employees = []
                error_message = " "
                if rec.is_vendor_payout and rec.batch_payout_line_ids:
                    # Employees violating vendor payout rules
                    employees = rec.batch_payout_line_ids.filtered(
                        lambda s: not s.employee_id.is_under_vendor or s.employee_id.is_under_vendor and s.employee_id.cashfree_payment
                    ).mapped('employee_id.name')
                    if employees:
                        error_message = (
                            "Selected driver's are not a payment to vendor. Please select payment to vendor without cashfree driver's."
                            if len(employees) > 1 else
                            "Selected driver is not a payment to vendor. Please select payment to vendor without cashfree driver's."
                        )
                elif not rec.is_vendor_payout and rec.batch_payout_line_ids:
                    # Employees violating non-vendor payout rules
                    employees = rec.batch_payout_line_ids.filtered(
                        lambda s: s.employee_id.is_under_vendor and not s.employee_id.cashfree_payment
                    ).mapped('employee_id.name')
                    if employees:
                        error_message = (
                            "Selected driver's are payment to vendor. Please select not a payment to vendor or cashfree payment driver's."
                            if len(employees) > 1 else
                            "Selected driver is payment to vendor. Please select not a payment to vendor or cashfree payment driver's."
                        )
                # Raise error if any employees are found
                if employees:
                    employee_list = "\n".join(employees)  # Construct the employee names
                    raise UserError(_(f"{error_message}\n{employee_list}"))

    # @api.onchange('region_id')
    # def region_id_validation_check(self):
    #     for rec in self:
    #         if rec.region_id and rec.batch_payout_line_ids and rec.region_id != rec.batch_payout_line_ids.employee_id.mapped('region_id'):
    #             raise ValidationError('Allowed drivers from the selected region only.')

    @api.depends('batch_payout_line_ids', 'batch_payout_line_ids.transfer_id')
    def get_payout_count(self):
        for rec in self:
            if rec.batch_payout_line_ids:
                rec.line_count = len(rec.batch_payout_line_ids)
            else:
                rec.line_count = 0

    @api.depends('batch_payout_line_ids', 'batch_payout_line_ids.total_payout')
    def get_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.batch_payout_line_ids.mapped('total_payout')) or 0.0

    @api.depends('bill_count','bill_ids')
    def _compute_bill_count(self):
        for rec in self:
            rec.bill_count = len(rec.bill_ids)

    def action_view_bill(self):
        for rec in self:
            tree_view = self.env.ref('account.view_in_invoice_bill_tree')
            form_view = self.env.ref('account.view_move_form')
            return{
                'name': _('Bill'),
                'res_model' : 'account.move',
                'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
                'view_mode' :'list,form',
                'context' : {},
                'domain' : [('id', 'in', rec.bill_ids.ids)],
                'target' : 'current',
                'type' : 'ir.actions.act_window',
            }

    def create_payout_line_payment_entry(self, line, accounts_data):
        if line.payment_state != 'success':
            if not line.payment_journal_id and line.total_payout >= 1.0:
                # Prepare move line entries
                move_line_list = [
                    {
                        'account_id': accounts_data.transfer_debit_account_id.id,
                        'debit': line.total_payout,
                        'credit': 0.0,
                        'name': 'Payout',
                        'partner_id': line.employee_id.related_partner_id.id if line.employee_id.related_partner_id else False,
                    },
                    {
                        'account_id': accounts_data.transfer_credit_account_id.id,
                        'debit': 0.0,
                        'credit': line.total_payout,
                        'name': 'Payout',
                    },
                ]

                # Prepare and create account move
                move_vals = {
                    'ref': self.name or '',
                    'line_ids': [(0, 0, ml) for ml in move_line_list],
                    'move_type': 'entry',
                    'region_id': self.region_id.id if self.region_id else False,
                    'journal_id': accounts_data.transfer_journal_id.id if accounts_data.transfer_journal_id else False,
                }
                move_id = self.env['account.move'].sudo().create(move_vals)
                move_id.action_post()
                line.payment_journal_id = move_id.id
            elif line.payment_journal_id and line.payment_journal_id.state == 'cancel':
                line.payment_journal_id.action_post()

    def create_trns_journal_entry(self):
        for rec in self:
            accounts_data = self.env['driver.payout.accounting.config'].sudo().search([],limit=1)
            if rec.batch_payout_line_ids and accounts_data:
                for payout_line in rec.batch_payout_line_ids:
                    rec.create_payout_line_payment_entry(payout_line,accounts_data)

    def create_exp_journal_entry(self):
        for rec in self:
            accounts_data = self.env['driver.payout.accounting.config'].sudo().search([], limit=1)
            if accounts_data or rec.batch_payout_line_ids:
                for line in rec.batch_payout_line_ids:
                    if not line.payable_journal_id:
                        move_line_list = [
                            (0, 0, {
                                'account_id': accounts_data.expense_debit_account_id.id,
                                'debit': line.daily_payout_amount + line.incentive_amount,
                                'credit': 0.0,
                                'analytic_distribution': {rec.region_id.analytic_account_id.id:100} or False,
                                'name': 'Payout',
                            })
                        ]
                        if line.total_payout:
                            move_line_list.append((0, 0, {
                                'account_id': accounts_data.expense_credit_account_id.id,
                                'debit': 0.0,
                                'credit': line.total_payout,
                                'name': 'Payout',
                                'partner_id': line.employee_id.related_partner_id.id if line.employee_id.related_partner_id else False,
                            }))

                        if line.deduction_amount and accounts_data.expense_deduction_account_id:
                            move_line_list.append((0, 0, {
                                'account_id': accounts_data.expense_deduction_account_id.id,
                                'debit': 0.0,
                                'credit': line.deduction_amount,
                                'name': 'Payout',
                                'partner_id': line.employee_id.related_partner_id.id if line.employee_id.related_partner_id else False,
                            }))

                        if line.tds_amount > 0.0 and accounts_data.tds_account_id:
                            move_line_list.append((0, 0, {
                                'account_id': accounts_data.tds_account_id.id,
                                'debit': 0.0,
                                'credit': line.tds_amount,
                                'name': 'Payout',
                                'partner_id': line.driver_partner_id.id if line.payment_vendor_acc and line.driver_partner_id else
                                (line.employee_id.related_partner_id.id if line.employee_id.related_partner_id else False),
                            }))

                        if move_line_list:
                            move_id = self.env['account.move'].sudo().create({
                                'ref': rec.name or '',
                                'line_ids': move_line_list,
                                'move_type': 'entry',
                                'region_id': rec.region_id.id if rec.region_id else False,
                                'journal_id': accounts_data.expense_journal_id.id if accounts_data.expense_journal_id else False,
                            })
                            move_id.action_post()
                            line.payable_journal_id = move_id.id
                            if not line.total_payout:
                                line.payment_state = "success"

                        if line.no_of_orders > 0:
                            no_of_orders = line.order_qty if line.order_qty > 0 else line.no_of_orders
                            order_cost = round((line.daily_payout_amount + line.incentive_amount) / no_of_orders, 2)
                            if order_cost != line.avg_order_cost:
                                line.avg_order_cost = order_cost
                                self.update_sales_order_cost(line)

    def get_ordered_data(self,data):
        ordered_data = {}
        if data:
            # Use defaultdict for simplifying nested dictionary handling
            ordered_data = defaultdict(lambda: defaultdict(lambda: {'daily_payout_amount': 0.0}))

            for rec in data:
                region_id = rec.get('region_id')
                employee_id = rec.get('employee_id')
                total_pay = rec.get('total_pay', 0.0)

                # Increment total_pay for the given region and employee
                ordered_data[region_id][employee_id]['daily_payout_amount'] += total_pay

        # Convert defaultdict back to a regular dict for returning
        return {region: dict(employees) for region, employees in ordered_data.items()}

    def action_cost_per_order(self):
        for rec in self:
            if rec.state in ('approve', 'pending', 'complete_with_fail', 'complete'):
                for line in rec.batch_payout_line_ids:
                    # Determine the number of orders
                    no_of_orders = line.order_qty if line.order_qty > 0 else line.no_of_orders
                    if no_of_orders > 0:
                        # Calculate the cost per order
                        line.avg_order_cost = (line.daily_payout_amount + line.incentive_amount) / no_of_orders
                        # Update sales order cost if valid
                        if line.avg_order_cost > 0:
                            rec.update_sales_order_cost(line)
            else:
                raise UserError(_('Please Select Approved Batches'))

    def update_sales_order_cost(self, line):
        for payout in line.daily_payout_ids:
            # Convert start and end dates to UTC strings
            start1 = datetime.combine(payout.date, datetime.min.time())
            end1 = start1 + timedelta(days=1)
            start, end = self.convert_to_utc(
                start1.strftime('%Y-%m-%d %H:%M:%S'),
                end1.strftime('%Y-%m-%d %H:%M:%S')
            )
            # Fetch sale order IDs matching the criteria
            query = """
                SELECT id FROM sale_order
                WHERE create_date >= %s AND create_date < %s
                  AND state != 'cancel'
                  AND driver_uid = %s
            """
            self.env.cr.execute(query, (start, end, payout.employee_id.driver_uid))
            so_ids = [row[0] for row in self.env.cr.fetchall()]  # Flatten results
            if so_ids:
                # Safely update the order costs using a parameterized query
                query = """
                    UPDATE sale_order
                    SET order_cost = %s
                    WHERE id IN %s
                """
                so_tuple_ids = tuple(so_ids) if len(so_ids) > 1 else (so_ids[0],)
                self.env.cr.execute(query, (line.avg_order_cost, so_tuple_ids))

    # Cashfree Batch payment

    def init_cashfree(self):
        """function to init the cashfree before making cashfree requests"""
        cashfree_id = self.env['cash.free.credentials'].sudo().search([("company_id", "=", self.company_id.id)],
                                                                      limit=1)
        if not cashfree_id:
            raise UserError("Cashfree configuration is missing, Please contact System Administrator")
        app_id, app_key = cashfree_id.payout_app_id, cashfree_id.payout_key
        env = self.env.company.cashfree_env
        Payouts.init(app_id, app_key, env, public_key=base64.b64decode(cashfree_id.public_key).decode('utf-8'))

    def get_line_status(self, transfer_id, payout_line):

        def cancel_transactions(line):
            """Helper to cancel related journal entries, invoices, and payments for the line."""
            if line.payment_journal_id:
                line.payment_journal_id.button_cancel()
            if line.payable_journal_id:
                line.payable_journal_id.button_cancel()

        def reset_line_entries(line):
            """Helper to reset line entries when not reinitiated."""
            if line.is_reinitiated != "yes":
                line.is_reinitiated = "no"
                if line.daily_payout_ids:
                    line.daily_payout_ids.write({'batch_payout_id': False})

        for rec in self:
            if transfer_id and payout_line:
                self.init_cashfree()
                try:
                    vals = None
                    get_transfer_status_response = Transfers.get_transfer_status(transferId=transfer_id)
                    json_data = json.loads(get_transfer_status_response.text)
                    transfer_data = json_data.get('data').get('transfer')

                    status = transfer_data.get('status')
                    processed_date = self.to_utc_datetime(transfer_data.get('processedOn')) or False
                    transaction_date = self.to_utc_datetime(transfer_data.get('addedOn')) or False
                    cashfree_ref = transfer_data.get('referenceId')
                    utr_ref = transfer_data.get('utr')
                    status_description = transfer_data.get('statusDescription')

                    if status == 'SUCCESS':
                        vals = {'payment_state': "success", 'processed_date': processed_date or transaction_date,
                                'transaction_date': transaction_date, 'cashfree_ref': cashfree_ref, 'utr_ref': utr_ref,
                                'status_description': status_description}
                    elif status in ('PENDING', 'PROCESSING'):
                        vals = {'payment_state': "pending", 'transaction_date': transaction_date,
                                'cashfree_ref': cashfree_ref, 'status_description': status_description}
                        if payout_line.payment_journal_id:
                            payout_line.payment_journal_id.button_cancel()
                    elif status == 'REVERSED':
                        vals = {'payment_state': "fail", 'processed_date': processed_date,
                                'transaction_date': transaction_date, 'cashfree_ref': cashfree_ref,
                                'status_description': status_description}
                        cancel_transactions(payout_line)
                        reset_line_entries(payout_line)
                    else:
                        vals = {'payment_state': "fail", 'processed_date': processed_date,
                                'transaction_date': transaction_date, 'cashfree_ref': cashfree_ref,
                                'status_description': status_description}
                        cancel_transactions(payout_line)
                        reset_line_entries(payout_line)

                    if vals:
                        payout_line.write(vals)

                except Exception as e:
                    raise ValidationError(_("Line Status Update Failed\nError: %s") % str(e))

    def action_check_status(self):
        for rec in self:
            if rec.state in ('pending', 'complete_with_fail', 'complete'):
                if not rec.transaction_date:
                    rec.check_state()
                else:
                    try:
                        for line in rec.batch_payout_line_ids:
                            if line.total_payout >= 1.0:
                                _logger.info("start status update in driver batch payout******************%s",
                                             line.transfer_id)
                                rec.get_line_status(line.transfer_id, line)
                                _logger.info("end status update in driver batch payout******************%s",
                                             line.transfer_id)
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

    def cash_free_batch_transfer(self, entries):
        self.init_cashfree()
        try:
            if entries:
                batch_tnx_create = Transfers.create_batch_transfer(batchTransferId=self.name,
                                                                   batchFormat="BENEFICIARY_ID",
                                                                   batch=entries, deleteBene=1)
                response = json.loads(batch_tnx_create.content)
                return response
        except Exception as e:
            error_string = repr(e)
            message = "Batch Payout Transfer Failed\nError:%s" % error_string
            raise ValidationError(_(message))

    def get_benef_details(self, cus_id):
        """function to get and validate partner(merchant) beneficiary details with cashfree """
        for rec in self:
            self.init_cashfree()
            try:
                bene_details = Beneficiary.get_bene_details(cus_id.beneficiary_uid)
                json_data = json.loads(bene_details.content)
                if 'status' in json_data and json_data['status'] == 'SUCCESS':
                    return
                else:
                    message = "%s Beneficiary[%s] Invalid" % (cus_id.name, cus_id.beneficiary_uid)
                    raise ValidationError(_(message))
            except Exception as e:
                message = "%s Beneficiary[%s] does not exist" % (cus_id.name, cus_id.beneficiary_uid)
                raise ValidationError(_(message))

    def action_batch_payment(self):
        for rec in self:
            try:
                query = "SELECT id FROM driver_batch_payout WHERE id = %s FOR UPDATE NOWAIT"
                self.env.cr.execute(query, (rec.id,))
            except OperationalError:
                raise UserError(
                    _('This record is currently being processed in another session. Please try again later.'))
            if rec.state == 'approve':
                entries = []
                non_benf_list = []
                if rec.batch_payout_line_ids:
                    # _logger.info("Beneficiary checking started in diver batch payout******************%s", rec.rec_name)
                    for line in rec.batch_payout_line_ids:
                        if line.total_payout >= 1.0:
                            if line.employee_id and line.employee_id.driver_partner_id and line.employee_id.is_under_vendor:
                                if line.employee_id.driver_partner_id.beneficiary:
                                    self.get_benef_details(line.employee_id)
                                    vals = {}
                                    vals.update({
                                        "transferId": line.transfer_id,
                                        "transferMode": "banktransfer",
                                        "beneId": line.employee_id.driver_partner_id.beneficiary or '',
                                        "amount": line.total_payout,

                                    })
                                    entries.append(vals)
                                else:
                                    non_benf_list.append(line.employee_id.name)
                            else:
                                if line.employee_id.beneficiary_uid:
                                    self.get_benef_details(line.employee_id)
                                    vals = {}
                                    vals.update({
                                        "transferId": line.transfer_id,
                                        "transferMode": "banktransfer",
                                        "beneId": line.employee_id.beneficiary_uid or '',
                                        "amount": line.total_payout,

                                    })
                                    entries.append(vals)
                                else:
                                    non_benf_list.append(line.employee_id.name)
                    # _logger.info("Beneficiary checking ended in driver batch payout******************%s", rec.rec_name)
                    if non_benf_list:
                        cus_names = ', '.join(non_benf_list)
                        raise UserError(_('Drivers [%s] have no Beneficiary In Cashfree' % (cus_names)))
                    else:
                        if entries:
                            batch_payment_res = rec.cash_free_batch_transfer(entries)

                            # _logger.info(
                            #     "%s Driver Payout Created **********************: %s" % (rec.rec_name, batch_payment_res))

                            if batch_payment_res.get('status') == 'SUCCESS':
                                rec.transaction_date = fields.datetime.now()
                                if batch_payment_res['data']['referenceId']:
                                    rec.cashfree_ref = batch_payment_res['data']['referenceId']
                                else:
                                    rec.cashfree_ref = ''
                            elif batch_payment_res.get('status') == 'PENDING':
                                rec.transaction_date = fields.datetime.now()
                            else:
                                raise ValidationError(_("Batch Transfer Failed\nError:%s", batch_payment_res))

                        if rec.batch_payout_line_ids:
                            rec.batch_payout_line_ids.write({'payment_state': 'initiate'})
                        rec.check_state()
            else:
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('%s batch payment is restricted.Payout is already in %s status.Please Refresh!' % (
                    rec.name, state)))

    def check_state(self):
        for rec in self:
            if rec.batch_payout_line_ids:
                # Update zero final pay records to 'success' state
                zero_values = rec.batch_payout_line_ids.filtered(lambda line: line.total_payout == 0.00)
                zero_values.write({'payment_state': "success"})

                non_success_lines = rec.batch_payout_line_ids.filtered(lambda line: line.payment_state != 'success')
                if non_success_lines:
                    # Check for any 'pending' or 'initiate' states within non-success lines
                    if any(line.payment_state in ('pending', 'initiate') for line in non_success_lines):
                        rec.state = 'pending'
                    else:
                        rec.state = 'complete_with_fail'
                else:
                    rec.state = 'complete'

    # Buttons

    def action_recompute_lines(self):
        def compute_total_pay_and_update(line):
            """Compute total pay and update related fields."""
            recs = line.daily_payout_ids or self.env['driver.payout'].search([
                ('employee_id', '=', line.employee_id.id),
                ('date', '>=', self.env.context.get('from_date')),
                ('date', '<=', self.env.context.get('to_date')),
                ('batch_payout_id', '=', False)
            ])
            if not line.daily_payout_ids and recs:
                line.daily_payout_ids = [(6, 0, recs.ids)]
                recs.write({'batch_payout_id': self.id})
            return sum(recs.mapped('total_payout')) if recs else 0.0

        def compute_incentive(line):
            """Compute incentive based on payout type."""
            no_of_orders = sum(line.daily_payout_ids.mapped('no_of_orders')) or sum(line.daily_payout_ids.mapped('order_qty'))
            worked_hours = sum(line.daily_payout_ids.mapped('worked_hours'))
            incentive_lines = (
                line.employee_id.plan_detail_id.weekly_incentive_ids if line.employee_id.payout_type == 'week'
                else line.employee_id.plan_detail_id.monthly_incentive_ids
            )
            return next((
                line.amount for line in incentive_lines
                if line.no_of_days <= len(line.payout_plan_id)
                   and line.min_hours <= worked_hours
                   and line.min_orders <= no_of_orders
            ), 0.0)

        for rec in self:
            if rec.state in ('draft', 'ready_verify', 'verify'):
                for line in rec.batch_payout_line_ids:
                    line.compute_payment_vals()
                    line.daily_payout_amount = compute_total_pay_and_update(line)
                    line.incentive_amount = compute_incentive(line)
                    line.tds_amount = line.deduction_amount = 0.0
                    line.total_revenue = sum(line.daily_payout_ids.mapped('total_revenue'))
                rec.get_total_amount()
            else:
                raise UserError(
                    _('Recompute lines is restricted. Payout {} is already in {} status. Please refresh!').format(
                        rec.name, dict(rec._fields['state'].selection).get(rec.state, '')
                    ))

    def action_compute_deduction(self):
        for rec in self:
            if rec.state != 'draft':
                state_name = dict(rec._fields['state'].selection).get(rec.state, rec.state)
                raise UserError(
                    _('%s compute deduction is restricted. Payout is already in %s status. Please Refresh!' % (
                    rec.name, state_name)))

            date = datetime.now().date()
            start = datetime.combine(date, datetime.min.time())
            end = start + timedelta(days=1)

            for line in rec.batch_payout_line_ids:
                query = self.env['account.move.line']._where_calc([
                    ('driver_uid', '=', line.driver_uid),
                    ('date', '<=', end.date()),
                    ('account_id.is_driver_account', '=', True),
                    ('parent_state', '=', 'posted'),
                    ('partner_id', '!=', False)
                ])
                from_clause, where_clause, where_clause_params = query.get_sql()
                sql = f"""
                    SELECT
                        SUM(account_move_line.debit) AS debit,
                        SUM(account_move_line.credit) AS credit
                    FROM {from_clause}
                    WHERE {where_clause}
                """
                self.env.cr.execute(sql, where_clause_params)
                balance = self.env.cr.dictfetchall() or {}
                balance = balance if isinstance(balance, dict) else balance[0]
                debit = balance.get('debit', 0.0) or 0.0
                credit = balance.get('credit', 0.0) or 0.0
                closing_bal = round(debit - credit, 2)

                total_payout = line.daily_payout_amount + line.incentive_amount - line.tds_amount
                diff_amt = round(total_payout - closing_bal, 2)
                line.deduction_amount = 0.0

                if closing_bal >= 1:
                    if diff_amt == 0.0 or diff_amt >= 1:
                        line.deduction_amount = closing_bal
                    elif diff_amt < 0:
                        line.deduction_amount = total_payout
                    elif 0 < diff_amt < 1:
                        line.deduction_amount = closing_bal - 1 if total_payout > closing_bal else total_payout

    def action_load_drivers(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('%s Payout has already been sent for verification. Please refresh!' % rec.name))
            rec.batch_payout_line_ids.unlink()
            # Fetch driver payouts matching the criteria
            driver_payouts = self.env['driver.payout'].search([
                ('employee_id.driver_partner_id', '=', rec.partner_id.id),
                ('employee_id.is_under_vendor', '=', True),
                ('employee_id.cashfree_payment', '=', False),
                ('region_id', '=', rec.region_id.id),
                ('date', '>=', rec.from_date),
                ('date', '<=', rec.to_date),
                ('batch_payout_id', '=', False)
            ])
            drivers = driver_payouts.mapped('employee_id')
            no_of_orders = 0
            incentive = 0
            for driver in drivers:
                driver_lines = driver_payouts.filtered(lambda s: s.employee_id.id == driver.id)
                # Calculate incentive based on weekly incentive lines
                for weekly_line in driver.plan_detail_id.weekly_incentive_ids:
                    no_of_orders = sum(driver_lines.mapped('order_qty'))
                    if sum(driver_lines.mapped('order_qty')) > 0:
                        no_of_orders = sum(driver_lines.mapped('order_qty'))
                    if weekly_line.no_of_days <= len(driver_lines) and weekly_line.min_hours <= sum(
                            driver_lines.mapped('worked_hours')) and weekly_line.min_orders <= no_of_orders:
                        incentive = weekly_line.amount
                values = {
                    'employee_id': driver.id,
                    'driver_uid': driver.driver_uid,
                    'order_qty': no_of_orders,
                    'daily_payout_amount': sum(driver_lines.mapped('total_payout')),
                    'incentive_amount': incentive,
                    'payment_state': 'initiate',
                    'daily_payout_ids': [(6, 0, driver_lines.ids)],
                }
                rec.write({'batch_payout_line_ids': [(0, 0, values)]})
                driver_lines.write({'batch_payout_id': rec.id})

    def set_to_draft(self):
        for rec in self:
            if rec.state in ('ready_verify','verify'):
                rec.state = "draft"
            else:
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('%s set to draft is restricted.Payout is already in %s status.Please Refresh!'%(rec.name,state)))

    def action_approve(self):
        for rec in self:
            if rec.state == 'verify':
                for line in rec.batch_payout_line_ids:
                    if line.total_payout < 0.0:
                        raise UserError(_('Transfer ID %s Total Payout is Negative'%(line.transfer_id)))
                    elif 0.00 < line.total_payout < 1.00:
                        raise UserError(_('Transfer ID %s Total Payout value can be 0 or greater than or equal to 1'%(line.transfer_id)))
                if not rec.is_vendor_payout:
                    rec.create_exp_journal_entry()
                rec.state = "approve"
                if rec.is_reject:
                    rec.is_reject =False
            else:
                raise UserError(_('%s Payout has been already approved.Please Refresh!'%rec.name))

    def _compute_transfer(self, rec):
        transfer_list = []
        for line in rec.batch_payout_line_ids:
            if line.total_payout < 0.0:
                raise UserError(_('Transfer ID %s Total Payout is Negative' % (line.transfer_id)))
            elif 0.00 < line.total_payout < 1.00:
                raise UserError(_('Transfer ID %s Total Payout value should be 0 or greater than or equal to 1' % (
                    line.transfer_id)))
            elif line.daily_payout_amount != round(sum(line.daily_payout_ids.mapped('total_payout')), 2):
                transfer_list.append(line.driver_uid + '-' + line.employee_id.name)
        if transfer_list:
            names = ' , '.join(transfer_list)
            string = 'Daily payout (A) amount is different from the amount in daily transaction for the below drivers:\n %s \nDo you want to recompute before proceeding?' % names
            return_do_wiz = self.env['send.verification.wizard'].create({'message': string})
            return {
                'name': _('Message'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'send.verification.wizard',
                'context': {'verify': True},
                'res_id': return_do_wiz.id,
                'target': 'new'
            }

    def action_verify(self):
        for rec in self:
            if rec.state == 'ready_verify':
                transfer_list = self._compute_transfer(rec)
                if transfer_list:
                    return transfer_list
                else:
                    rec.update_verify()
                # compute_transfer = transfer_list if transfer_list else rec.update_verify()
            else:
                state = rec.state and dict(rec._fields['state'].selection).get(rec.state) or ''
                raise UserError(_('%s Payout has been already verified.Please Refresh!'%rec.name))

    def action_ready_to_verify(self):
        for rec in self:
            if rec.state == 'draft':
                transfer_list = self._compute_transfer(rec)
                if transfer_list:
                    return transfer_list
                else:
                    rec.update_ready_to_verify()
              # find cost per order
                for line in rec.batch_payout_line_ids:
                    if line.no_of_orders > 0:
                        no_of_orders = line.no_of_orders
                        if line.order_qty > 0:
                            no_of_orders = line.order_qty
                        line.avg_order_cost = (line.daily_payout_amount + line.incentive_amount) / no_of_orders
                        if line.avg_order_cost > 0:
                            self.update_sales_order_cost(line)
            else:
                raise UserError(_('%s Payout has been already send for verification.Please Refresh!' % rec.name))

    def update_ready_to_verify(self):
        for rec in self:
            rec.state = "ready_verify"
            template = self.env.ref('driver_management.batch_payout_send_for_verify_template', raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True)

    def update_verify(self):
        for rec in self:
            rec.state = "verify"
            template = self.env.ref('driver_management.batch_payout_send_for_verify_template', raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True)

    def get_payout_group_users(self):
        mail = []
        joined_string = ""
        payout_verify_group = self.env.ref('driver_management.group_verify_payout')
        if payout_verify_group:
            for user in payout_verify_group.users:
                mail.append(user.partner_id.email or '')
        payout_approval_group = self.env.ref('driver_management.group_approve_payout')
        if payout_approval_group:
            for user in payout_approval_group.users:
                mail.append(user.partner_id.email or '')
        if mail:
            joined_string = ",".join(mail)
        return joined_string

    # Schedulers

    @api.model
    def compute_payout(self, payout_type, data, trans_date_field):
        """Generic method to compute payouts."""
        date_begin = None
        if data and payout_type == 'week':
            date_begin = data.weekly_trans_date + timedelta(days=1)
        elif data and payout_type == 'month':
            date_begin = data.monthly_trans_date + timedelta(days=1)
        else:
            date_begin = trans_date_field + timedelta(days=1)
        date_end = (date_begin + (timedelta(days=6) if payout_type == 'week' else relativedelta(months=1) - relativedelta(days=1)))

        query = f"""
            SELECT 
                dp.region_id AS region_id, SUM(dp.total_payout) AS total_pay, dp.employee_id AS employee_id
            FROM driver_payout dp
            JOIN hr_employee emp ON dp.employee_id = emp.id
            WHERE dp.date BETWEEN '{date_begin}' AND '{date_end}'
              AND emp.payout_type = '{payout_type}' AND dp.batch_payout_id IS NULL
            GROUP BY dp.region_id, dp.employee_id
        """
        self.env.cr.execute(query)
        qry_data = self.env.cr.dictfetchall()

        grouped_data = self.get_ordered_data(qry_data)
        if not grouped_data:
            return

        for region_id, employee_data in grouped_data.items():
            line_vals = self._prepare_payout_lines(employee_data, date_begin, date_end, payout_type)
            if line_vals:
                region = self.env['sales.region'].sudo().browse(region_id)
                description = f"{payout_type.capitalize()} payout of {region.name} from {date_begin} to {date_end}."
                payout = self.env['driver.batch.payout'].sudo().create({
                    'region_id': region_id,
                    'description': description,
                    'from_date': date_begin,
                    'to_date': date_end,
                    'batch_payout_line_ids': line_vals,
                    'is_cron_created': True,
                })
                self._update_driver_payouts(payout)

    @api.model
    def _prepare_payout_lines(self, employee_data, date_begin, date_end, payout_type):
        """Prepare line items for payouts."""
        line_vals = []
        for employee_id, employee_info in employee_data.items():
            employee = self.env['hr.employee'].sudo().browse(employee_id)
            if not employee.is_under_vendor or (employee.is_under_vendor and employee.cashfree_payment):
                vals = {
                    'from_date': date_begin,
                    'to_date': date_end,
                    'employee_id': employee_id,
                    'driver_partner_id': employee.related_partner_id.id if employee.related_partner_id else False,
                    'payment_vendor_acc': False,
                    'pan_no': employee.pan_no,
                    'daily_payout_amount': employee_info['daily_payout_amount'] or 0.0,
                }
                if employee.is_under_vendor and employee.driver_partner_id:
                    vals.update({
                        'driver_partner_id': employee.driver_partner_id.id,
                        'payment_vendor_acc': employee.is_under_vendor,
                        'pan_no': employee.driver_partner_id.l10n_in_pan,
                    })
                line_vals.append((0, 0, vals))
        return line_vals

    @api.model
    def _update_driver_payouts(self, payout):
        """Update driver payouts and incentives."""
        for line in payout.batch_payout_line_ids:
            recs = self.env['driver.payout'].search([
                ('employee_id', '=', line.employee_id.id),
                ('date', '>=', line.from_date),
                ('date', '<=', line.to_date),
                ('batch_payout_id', '=', False)
            ])
            line.daily_payout_ids = [(6, 0, recs.ids)] if recs else []
            if line.employee_id.plan_detail_id:
                incentive_lines = (line.employee_id.plan_detail_id.weekly_incentive_ids if
                                   line.employee_id.payout_type == 'week' else
                                   line.employee_id.plan_detail_id.monthly_incentive_ids)
                line.incentive_amount = self._compute_incentive(recs, incentive_lines)
            for payout_line in recs:
                payout_line.batch_payout_id = payout.id

    @api.model
    def _compute_incentive(self, recs, incentive_lines):
        """Compute incentives based on incentive lines."""
        if not recs or not incentive_lines:
            return 0.0
        no_of_orders = sum(recs.mapped('no_of_orders')) or sum(recs.mapped('order_qty'))
        worked_hours = sum(recs.mapped('worked_hours'))
        for line in incentive_lines:
            if (
                    line.no_of_days <= len(recs) and
                    line.min_hours <= worked_hours and
                    line.min_orders <= no_of_orders
            ):
                return line.amount
        return 0.0

    @api.model
    def total_weekly_pay(self):
        """Compute weekly payouts."""
        data = self.env['driver.payout.date.config'].sudo().search([], limit=1)
        if not data or not data.weekly_trans_date:
            return
        self.compute_payout(payout_type='week', data=data, trans_date_field='weekly_trans_date')
        data.weekly_trans_date = data.weekly_trans_date + timedelta(days=7)

    @api.model
    def total_monthly_pay(self):
        data = self.env['driver.payout.date.config'].sudo().search([], limit=1)
        if not data or not data.monthly_trans_date:
            return
        """Compute monthly payouts."""
        self.compute_payout(payout_type='month', data=data, trans_date_field='monthly_trans_date')
        month_beg = data.monthly_trans_date + timedelta(days=1)
        date_rec = month_beg + relativedelta(months=1) - timedelta(days=1)
        data.monthly_trans_date = date_rec

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
    def pending_payout_status(self):
        data = self.env['driver.payout.date.config'].sudo().search([], limit=1)
        if data and data.payout_status_date:
            payout_line_ids = self.env['driver.batch.payout.lines'].sudo().search(
                [('payment_state', 'in', ('initiate', 'pending')), ('batch_payout_id.state', '=', 'pending'),
                 ('batch_payout_id.is_vendor_payout', '=', False)], order='batch_payout_id asc',
                limit=data.pending_payout_limit)
            for line in payout_line_ids:
                line.batch_payout_id.get_line_status(line.transfer_id, line)
                accounts_data = self.env['driver.payout.accounting.config'].sudo().search([], limit=1)
                line.batch_payout_id.create_payout_line_payment_entry(line, accounts_data)
                line.batch_payout_id.check_state()

            data.pending_payout_sts_date = fields.Date.today()

    # This method is called to create intermediate table of  completed and completed with failure weekly payout by a cron task
    @api.model
    def action_create_complete_payout(self):
        data = self.env['driver.payout.date.config'].sudo().search([], limit=1)
        if data and data.payout_status_date:
            current_date = data.payout_status_date + timedelta(days=1)
            new_date = current_date + timedelta(days=-8)
            date_from = datetime.combine(new_date, datetime.min.time())
            start, end = self.get_start_and_end(date_from.strftime("%Y-%m-%d %H:%M:%S"))
            utc_date_from = self.to_utc_datetime(end.strftime("%Y-%m-%d %H:%M:%S"))
            payout_ids = self.sudo().search(
                [('transaction_date', '>=', utc_date_from), ('state', 'in', ('complete_with_fail', 'complete')),
                 ('is_vendor_payout', '=', False)], order='id asc')
            payout_status_update_ids = self.env['payout.status.update'].search([('is_check', '=', True)])
            if payout_status_update_ids:
                if len(payout_status_update_ids) == 1:
                    self.env.cr.execute(
                        """DELETE FROM payout_status_update WHERE id = %s;""" % str(payout_status_update_ids.id))
                else:
                    self.env.cr.execute(
                        """DELETE FROM payout_status_update WHERE id in %s;""" % (tuple(payout_status_update_ids.ids),))

            if payout_ids:

                for payout in payout_ids:
                    payout_status_update_id = self.env['payout.status.update'].search(
                        [('batch_payout_id', '=', payout.id), ('is_check', '=', False)])
                    if not payout_status_update_id:
                        payout_status_update = self.env['payout.status.update'].create({'batch_payout_id': payout.id})

            data.payout_status_date = current_date

        # This method is called to update status of completed and completed with failure weekly payout by a cron task

    @api.model
    def daily_payout_status(self):
        payout_status_ids = self.env['payout.status.update'].search([('is_check', '=', False)], limit=50,
                                                                    order='id asc')
        for line in payout_status_ids:
            line.batch_payout_id.action_check_status()
            line.is_check = True

    def action_create_bill(self):
        for rec in self:
            count = self.env['driver.payout'].search_count([('batch_payout_id', '=', rec.id)])
            line_list = []
            payout_config_id = self.env['driver.payout.accounting.config'].sudo().search([], limit=1)
            if rec.batch_payout_line_ids:
                total_amount = (sum(rec.batch_payout_line_ids.mapped('daily_payout_amount')) or 0.0) + (
                        sum(rec.batch_payout_line_ids.mapped('incentive_amount')) or 0.0)
                new_dict = {
                    'name': 'Charges towards the driver payout b/w %s to %s \nTotal no. of driver payout : %s'
                            % (rec.from_date.strftime('%d/%m/%y'), rec.to_date.strftime('%d/%m/%y'), count),
                    'price_unit': total_amount,
                    'analytic_distribution': {rec.partner_id.region_id.analytic_account_id.id: 100} or False,
                    'account_id': payout_config_id.expense_debit_account_id.id,
                    'tax_ids': [(6, 0, [rec.partner_id.tax_tds_id.id])] if rec.partner_id.tax_tds_id else False,
                }
                line_list.append((0, 0, new_dict))
                total_deduction_amount = sum(rec.batch_payout_line_ids.mapped('deduction_amount')) or 0.0
                if total_deduction_amount > 0:
                    new_dict = {
                        'name': 'Driver deductions',
                        'price_unit': -(total_deduction_amount),
                        'account_id': payout_config_id.vendor_payout_account_id.id,
                    }
                    line_list.append((0, 0, new_dict))
            state_journal = self.env['state.journal'].search([('state_id', '=', rec.partner_id.region_id.state_id.id)])
            if not state_journal.vendor_bill_journal_id:
                raise UserError(_("Please add bill journal in %s state!!!") % (rec.partner_id.region_id.state_id.name))
            bill = self.env['account.move'].create({
                'move_type': 'in_invoice',
                'journal_id': state_journal.vendor_bill_journal_id.id,
                'invoice_date': date.today(),
                'partner_id': rec.partner_id.id,
                'state': 'draft',
                'vendor_payout_id': rec.id,
                'invoice_line_ids': line_list,
                'line_count': count,
                'invoice_origin': rec.name,
            })
            rec.bill_ids = [(4, bill.id, False)]
            rec.state = 'pending'
            rec.batch_payout_line_ids.write({"payment_state": "pending"})
            if rec.batch_payout_line_ids and total_deduction_amount > 0:
                move_line_list = []
                move_line = {'account_id': payout_config_id.vendor_payout_account_id.id or False,
                             'debit': total_deduction_amount,
                             'credit': 0.0,
                             # 'name':'Payout',
                             'partner_id': rec.partner_id.id,
                             }
                move_line_list.append((0, 0, move_line))
                for pay_line in rec.batch_payout_line_ids:
                    move_line_1 = {'account_id': payout_config_id.expense_deduction_account_id.id or False,
                                   'debit': 0.0,
                                   'credit': pay_line.deduction_amount,
                                   'partner_id': pay_line.employee_id.related_partner_id.id,
                                   }

                    move_line_list.append((0, 0, move_line_1))

                vals = {
                    'ref': rec.name or '',
                    'line_ids': move_line_list,
                    'move_type': 'entry',
                    'region_id': rec.region_id and rec.region_id.id or False,
                    'journal_id': payout_config_id.expense_journal_id and payout_config_id.expense_journal_id.id or False,
                }

                move_id = self.env['account.move'].sudo().create(vals)
                move_id.action_post()
                rec.deduction_entry_id = move_id.id
            tree_view = self.env.ref('account.view_in_invoice_bill_tree')
            form_view = self.env.ref('account.view_move_form')
            return {
                'name': _('Bill'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
                'domain': [('id', '=', bill.id)],
                'context': {},
                'target': 'current',
            }

    def print_xlsx(self):
        for rec in self:
            data = {
                'ids': self.env.context.get('active_ids', []),
                'model': 'driver.batch.payout',
            }
            report = self.env.ref('driver_management.week_month_xlsx')
            report.report_file = "QWQER_Driver_Payout - %s" % (self.name or '')
            return self.env.ref('driver_management.week_month_xlsx').report_action(self, data=data)