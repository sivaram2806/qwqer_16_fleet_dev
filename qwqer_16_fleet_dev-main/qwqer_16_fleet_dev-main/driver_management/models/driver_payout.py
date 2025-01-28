# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError
from lxml import etree
import pytz

STATUS = [
    ('draft', 'Draft'),
    ('ready_verify', 'Ready For Verification'),
    ('verify', 'Verified'),
    ('approve', 'Approved'),
    ('pending', 'Pending'),
    ('complete_with_fail', 'Completed With Failures'),
    ('complete', 'Completed'),
    ('cancel', 'Cancelled')
]


class DriverPayout(models.Model):
    """
    Model contains records driver.payout
    """
    _name = 'driver.payout'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread']
    _order = 'date desc'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(DriverPayout, self).get_view(view_id=view_id, view_type=view_type, **options)

        doc = etree.XML(res['arch'])
        if view_type == 'form' or view_type == "tree":
            if not self.env.user.has_group('driver_management.group_edit_create_payout'):
                for node_form in doc.xpath("//form"):
                    node_form.set("edit", 'false')
            if not self.env.user.has_group('base.group_system'):
                for node_form in doc.xpath("//form"):
                    node_form.set("delete", 'false')
                for node_form in doc.xpath("//tree"):
                    node_form.set("delete", 'false')
        res['arch'] = etree.tostring(doc)
        return res

    employee_id = fields.Many2one('hr.employee', string="Driver", domain="[('company_id','=',company_id)]")
    driver_uid = fields.Char('Driver ID', index=True)  # V13_field: employee_code
    date = fields.Date("Date")
    region_id = fields.Many2one('sales.region', string="Region", domain="[('company_id','=',company_id)]")
    minimum_wage = fields.Float(string='Minimum wage', compute='compute_orders_hours_incentive',
                                store=True)  # V13_field: base_pay
    worked_hours = fields.Float(string='Worked Hours', tracking=True)
    total_revenue = fields.Float(string='Total Revenue')
    total_distance = fields.Float(string='Total Dist', tracking=True)  # V13_field: app_total_distance
    total_estimated_distance = fields.Float(string='Total Est: Dist')  # V13_field: total_distance
    order_km_incentive = fields.Float(string='Incentive Order KM', compute='compute_distance_incentive',
                                      store=True)  # V13_field: order_amount
    day_km_incentive = fields.Float(string='Incentive Day KM', compute='compute_distance_incentive',
                                    store=True)  # V13_field: day_amount
    orders_incentive = fields.Float(string='Daily Incentive(Orders)', compute='compute_orders_hours_incentive',
                                    store=True)  # V13_field: orders_pay
    hours_incentive = fields.Float(string='Daily Incentive (Hours)', compute='compute_orders_hours_incentive',
                                   store=True)  # V13_field: hours_pay
    stop_count_incentive = fields.Float(string='Daily Incentive (Stop Count)')  # V13_field: stopcount_pay
    holiday_incentive = fields.Float(string='Holiday Bonus')  # V13_field: weekend_pay
    no_of_orders = fields.Integer("No:of Orders")  # V13_field: orders
    total_payout = fields.Float(string='Total Payout', compute='compute_total_payout', store=True,
                                digits='Product Price')  # V13_field: total_pay
    vehicle_category_id = fields.Many2one('driver.vehicle.category', string='Vehicle Category',
                                          store=True)  # V13_field: vehicle_cteg_id
    status = fields.Selection(STATUS, string='Status', default=False, store=True, related="batch_payout_id.state",
                              tracking=True)  # V13_field: state
    order_qty = fields.Integer("Order Quantity")
    batch_payout_id = fields.Many2one('driver.batch.payout', string="Batch Transfer")
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

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

    def get_sale_orders(self, start, end, driver_id):
        """
         Get the sale orders of the driver having create date greater than or equal to start and lesser
         than end and state not equal to cancel
        """
        if self.env.context.get("with_order_date"):
            return self.env['sale.order'].sudo().search([
            ('date_order', '>=', start),
            ('date_order', '<', end),
            ('state', '!=', 'cancel'),
            ('driver_id', '=', driver_id)
        ])
        return self.env['sale.order'].sudo().search([
            ('create_date', '>=', start),
            ('create_date', '<', end),
            ('state', '!=', 'cancel'),
            ('driver_id', '=', driver_id)
        ])

    @api.depends('worked_hours', 'no_of_orders', 'order_qty')
    def compute_orders_hours_incentive(self):  # V13_method: get_bonus
        """
        Compute the Daily Incentive(Orders) and Daily Incentive(Hours) in depends with the worked_hours,no_of_orders and order_qty
        """
        for rec in self:
            rec.hours_incentive = rec.orders_incentive = rec.minimum_wage = sum_amount = 0.0
            # Checking whether driver is set in the transaction and whether a plan is set to the driver
            if rec.employee_id and rec.employee_id.plan_detail_id:
                plan = rec.employee_id.plan_detail_id
                rec.minimum_wage = self.compute_minimum_wage(plan, rec.worked_hours, rec.no_of_orders, rec.order_qty)
                rec_len = len(plan.daily_incentive_per_hours_ids)
                # Checking whether Daily Incentive Per Hour is configured in the plan
                if plan.daily_incentive_per_hours_ids:
                    for index, incentives in enumerate(plan.daily_incentive_per_hours_ids, start=1):
                        rec.hours_incentive += self.compute_incentive_pay(rec.worked_hours, rec_len, index,
                                                                         incentives.min_hours, incentives.max_hours,
                                                                         incentives.amount_per_hour, sum_amount)

                # Checking whether Daily Incentive Per Order is configured in the plan
                if plan.daily_incentive_per_order_ids:
                    order_count = rec.order_qty if rec.order_qty > 0 else rec.no_of_orders
                    for line in plan.daily_incentive_per_order_ids:
                        rec.orders_incentive += self.compute_sum_amount(order_count, line.amount_per_order,
                                                                       line.min_orders, line.max_orders)

    @api.depends('total_estimated_distance', 'total_distance')
    def compute_distance_incentive(self):  # V13_method: get_incentive
        """
        Compute Distance Incentives depending with the total_distance and total_estimated_distance
        """
        for rec in self:
            rec.day_km_incentive = rec.order_km_incentive = total_pay = 0.0
            # Checking whether driver is set in the transaction and whether a plan is set to the driver
            if rec.employee_id and rec.employee_id.plan_detail_id:
                plan = rec.employee_id.plan_detail_id
                # Checking whether Incentive Order Km is configured in the plan
                if plan.incentive_order_km_ids:
                    start, end = self.convert_to_utc(
                        datetime.combine(rec.date, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S'),
                        (datetime.combine(rec.date, datetime.min.time()) + timedelta(days=1)).strftime(
                            '%Y-%m-%d %H:%M:%S')
                    )
                    so_ids = self.get_sale_orders(start, end, rec.employee_id.id)
                    plan_order_len = len(plan.incentive_order_km_ids)
                    for so_rec in so_ids:
                        for index, incentive in enumerate(plan.incentive_order_km_ids, start=1):
                            rec.order_km_incentive += self.compute_incentive_pay(so_rec.estimated_distance,
                                                                                 plan_order_len,
                                                                                 index, incentive.start_km,
                                                                                 incentive.end_km,
                                                                                 incentive.amount)

                # Checking whether Incentive Day Km is configured in the plan
                if plan.day_incentive_order_km_ids:
                    plan_km_len = len(plan.day_incentive_order_km_ids)
                    for index, incentive in enumerate(plan.day_incentive_order_km_ids, start=1):
                        rec.day_km_incentive += self.compute_incentive_pay(rec.total_distance, plan_km_len, index,
                                                                          incentive.start_km, incentive.end_km,
                                                                          incentive.amount)
            else:
                rec.day_km_incentive = rec.order_km_incentive = 0.0

    def get_stopcount_pay(self):
        """
        Compute Stop count incentive depending according to the stop count value inside the sale order
        """
        for rec in self:
            sum_amount = 0.0
            plan = rec.employee_id.plan_detail_id

            if plan and plan.daily_incentive_stop_count_ids:
                # Convert to UTC and fetch sale orders
                start, end = self.convert_to_utc(
                    datetime.combine(rec.date, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S'),
                    (datetime.combine(rec.date, datetime.min.time()) + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                )
                so_ids = self.get_sale_orders(start, end, rec.employee_id.id)

                total_stopcount = sum(map(int, so_ids.mapped('stop_count'))) or 0

                # Calculate pay based on stop count
                for line in plan.daily_incentive_stop_count_ids:
                    sum_amount += rec.compute_sum_amount(total_stopcount, line.amount_per_stop_count, line.start_count,
                                                        line.end_count)

            return sum_amount

    def compute_sum_amount(self, total_count, minimum_amount, min_value, max_value, sum_amount=0):
        """
        Compute the incentive amounts
        """
        if (total_count - min_value) >= 0.0:
            if min_value == 0:
                if total_count > max_value:
                    sum_amount += (minimum_amount * (max_value - min_value))
                else:
                    sum_amount += (minimum_amount * (total_count - min_value))
            else:
                if total_count > max_value:
                    sum_amount += (minimum_amount * ((max_value - min_value) + 1))
                else:
                    sum_amount += (minimum_amount * ((total_count - min_value) + 1))
        return sum_amount

    def compute_incentive_pay(self, avg_value, plan_len, index, min_value, max_value, minimum_wage, total_pay=0.0):
        """
        Compute the incentive amounts
        """
        if (avg_value - min_value) >= 0.0:
            if avg_value > max_value:
                if index == plan_len:
                    total_pay += (minimum_wage * (avg_value - min_value))
                else:
                    total_pay += (minimum_wage * (max_value - min_value))
            else:
                total_pay += (minimum_wage * (avg_value - min_value))
        return total_pay

    def compute_minimum_wage(self, plan, hrs, orders, order_qty):
        """
        Compute the minimum wage configured in the plan
        """
        min_amount = 0.0
        no_of_orders = order_qty if order_qty > 0 else orders
        for line in plan.driver_minimum_wage_ids:
            if line.min_hrs <= hrs and line.min_orders <= no_of_orders:
                min_amount = line.min_amount
        return min_amount  # Default value if no conditions are met

    @api.depends('minimum_wage', 'order_km_incentive', 'day_km_incentive', 'orders_incentive',
                 'hours_incentive', 'holiday_incentive', 'stop_count_incentive')
    def compute_total_payout(self):
        for rec in self:
            rec.total_payout = (rec.minimum_wage + rec.order_km_incentive + rec.day_km_incentive + rec.orders_incentive
                                + rec.hours_incentive + rec.holiday_incentive + rec.stop_count_incentive)

    def get_so_details(self, current_date, driver_id):
        """
        Get sale order details
        Args:
            current_date (datetime): Current datetime.
            driver_id (id): Driver Id.

        Returns:
            tuple: A tuple containing sum of estimated distance,amount total,total product qty and len of sale orders
        """
        if current_date and driver_id:
            start = datetime.combine(current_date, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
            end = (datetime.combine(current_date, datetime.min.time()) + timedelta(days=1)).strftime(
                '%Y-%m-%d %H:%M:%S')
            start, end = self.convert_to_utc(start, end)

            so_ids = self.get_sale_orders(start, end, driver_id)
            if so_ids:
                return (
                    sum(so_ids.mapped('estimated_distance')),
                    len(so_ids),
                    sum(so_ids.mapped('amount_total')),
                    sum(so_ids.mapped('total_product_qty'))
                )
        return 0, 0, 0, 0

    def action_recompute(self):
        """
        Button to recompute the values of incentives after setting a new plan for the driver.
        """
        for rec in self:
            if not rec.status or rec.status  in ('draft','ready_verify','verify'):
                incentives = self.calculate_employee_incentives(rec.employee_id.id, rec.employee_id.plan_detail_id, rec)

                rec.write({
                    'total_estimated_distance': incentives['total_distance'],
                    'no_of_orders': incentives['order_count'],
                    'total_revenue': incentives['total_revenue'],
                    'order_qty': incentives['order_qty'],
                    'stop_count_incentive': incentives['stop_count_incentive'],
                    'holiday_incentive': incentives['holiday_incentive'] or incentives['weekend_incentive'],
                    'region_id': rec.employee_id.region_id and rec.employee_id.region_id.id,
                })
                rec.compute_distance_incentive()
                rec.compute_orders_hours_incentive()
            else:
                raise ValidationError(_("Recompute should be performed in Draft or Verified state"))

    def driver_total_pay_cron(self):
        """Method used to call Driver total pay"""
        # Method triggered by cron task
        companies = self.env['res.company'].search([])
        for company in companies:
            payout_config_id = self.env['driver.payout.date.config'].search([('company_id','=',company.id)], limit=1)
            if payout_config_id and payout_config_id.daily_trans_date:
                last_date = payout_config_id.daily_trans_date + timedelta(days=1)
                self.driver_total_pay(payout_config_id, last_date,update_last_exec_date=True)

    @api.model
    def driver_total_pay(self, payout_config_id, last_date,update_last_exec_date=False):
        """
        Method used to create daily driver transaction based on driver attendances.
        """

        if payout_config_id and last_date:
            attendance_records = self.env['hr.attendance'].sudo().search(
                [('date', '=', last_date), ('daily_payout_id', '=', False)]
            )
            if attendance_records:
                attendance_data = {}
                for record in attendance_records:
                    emp_id = record.employee_id.id
                    if emp_id not in attendance_data:
                        attendance_data[emp_id] = {
                            'date': record.date,
                            'driver_uid': record.employee_id.driver_uid,
                            'plan_id': record.employee_id.plan_detail_id,
                            'worked_hours': record.app_working_hours,
                            'app_total_distance': record.app_total_distance,
                            'attendance_ids': [record.id],
                            'region_id': record.employee_id.region_id.id,
                            'vehicle_category_id': record.employee_id.vehicle_category_id.id,
                        }
                    else:
                        attendance_data[emp_id]['worked_hours'] += record.app_working_hours
                        attendance_data[emp_id]['app_total_distance'] += record.app_total_distance
                        attendance_data[emp_id]['attendance_ids'].append(record.id)

                if attendance_data:
                    for emp_id, data in attendance_data.items():
                        payout = self.env['driver.payout'].create({
                            'employee_id': emp_id,
                            'driver_uid': data['driver_uid'],
                            'region_id': data['region_id'],
                            'date': data['date'],
                            'worked_hours': data['worked_hours'],
                            'total_distance': data['app_total_distance'],
                        })

                        incentives = self.calculate_employee_incentives(emp_id, data['plan_id'], payout)

                        payout.write({
                            'total_estimated_distance': incentives['total_distance'],
                            'no_of_orders': incentives['order_count'],
                            'order_qty': incentives['order_qty'],
                            'total_revenue': incentives['total_revenue'],
                            'stop_count_incentive': incentives['stop_count_incentive'],
                            'holiday_incentive': incentives['holiday_incentive'] or incentives['weekend_incentive'],
                        })
                        # Link attendance records to payout
                        self.env['hr.attendance'].sudo().browse(data['attendance_ids']).write(
                            {'daily_payout_id': payout.id})
            if update_last_exec_date:
                payout_config_id.daily_trans_date = last_date

    def driver_so_daily_transaction_cron(self):
        """Method used to call So daily driver Transaction"""
        # Calculate start and end datetime in UTC
        companies = self.env['res.company'].search([])
        for company in companies:
            payout_config_id = self.env['driver.payout.date.config'].search([('company_id','=',company.id)], limit=1)
            if payout_config_id and payout_config_id.so_daily_trans_date:
                last_date = payout_config_id.so_daily_trans_date + timedelta(days=1)
                self.driver_so_daily_transaction(payout_config_id, last_date,driver_so_daily_transaction=True)

    def driver_so_daily_transaction(self, payout_config_id, last_date,driver_so_daily_transaction=False):
        """
        Method used to create daily transaction based on Sale orders got for a driver.
        """

        start1 = datetime.combine(last_date, datetime.min.time())
        end1 = start1 + timedelta(days=1)
        start, end = self.convert_to_utc(
            start1.strftime('%Y-%m-%d %H:%M:%S'),
            end1.strftime('%Y-%m-%d %H:%M:%S')
        )

        # Prepare domain for sales orders
        attendance_ids = self.env['hr.attendance'].sudo().search([('date', '=', last_date)])
        domain = [
            ('create_date', '>=', start),
            ('create_date', '<', end),
            ('state', '!=', 'cancel'),
            ('driver_id', '!=', False),
            ('driver_payout_id', '=', False)
        ]
        if self.env.context.get("with_order_date"):
            domain = [
                ('date_order', '>=', start),
                ('date_order', '<', end),
                ('state', '!=', 'cancel'),
                ('driver_id', '!=', False),
                ('driver_payout_id', '=', False)
            ]

        if attendance_ids:
            attendance_employee_ids = attendance_ids.mapped('employee_id')
            domain.append(('driver_id', 'not in', attendance_employee_ids.ids))

        # Query sales order data
        so_search = self.env['sale.order']._where_calc(domain)
        from_clause, where_clause, where_clause_params = so_search.get_sql()
        so_sql = f"""
                SELECT 
                    sale_order.driver_id as driver_id,
                    count(sale_order.id) as orders,
                    sum(sale_order.total_product_qty) as order_qty,
                    sum(sale_order.amount_total) as total_revenue,
                    COALESCE(sum(sale_order.estimated_distance), 0) as estimated_distance
                FROM {from_clause} WHERE {where_clause} GROUP BY sale_order.driver_id
            """

        self.env.cr.execute(so_sql, where_clause_params)
        qry_data = self.env.cr.dictfetchall()

        # Process queried data
        if qry_data:
            for so_data in qry_data:
                existing_payout = self.env['driver.payout'].sudo().search([
                    ('date', '=', last_date),
                    ('employee_id', '=', so_data['driver_id'])
                ])

                if not existing_payout:
                    driver_id = self.env['hr.employee'].sudo().browse(so_data['driver_id'])
                    plan = driver_id.plan_detail_id

                    # Create new payout record
                    payout_id = self.env['driver.payout'].sudo().create({
                        'employee_id': driver_id.id,
                        'driver_uid': driver_id.driver_uid,
                        'region_id': driver_id.region_id.id,
                        'vehicle_category_id': driver_id.vehicle_category_id.id,
                        'date': last_date,
                        'total_estimated_distance': so_data['estimated_distance'],
                        'total_revenue': so_data['total_revenue'],
                        'no_of_orders': so_data['orders'],
                        'order_qty': so_data['order_qty'],
                    })

                    # Calculate incentives
                    if payout_id and plan:
                        incentives = self.calculate_employee_incentives(driver_id.id, plan, payout_id)

                        # Update payout record with incentives
                        payout_id.write({
                            'stop_count_incentive': incentives['stop_count_incentive'],
                            'holiday_incentive': incentives['holiday_incentive'] or incentives['weekend_incentive'],
                        })

                    # Link sales orders to the payout
                    so_ids = self.get_sale_orders(start, end, driver_id.id)
                    so_ids.driver_payout_id = payout_id.id

        # Update configuration date
        if driver_so_daily_transaction:
            payout_config_id.so_daily_trans_date = last_date

    def calculate_employee_incentives(self, driver_id, plan, payout):
        """
        Calculates incentives and details based on given parameters.
        """
        current_date = datetime.combine(payout.date, datetime.min.time())
        total_distance, order_count, total_revenue, total_qty = self.get_so_details(current_date, driver_id)
        stop_count_incentive = 0.0
        holiday_incentive = 0.0
        weekend_incentive = 0.0

        if driver_id and plan:
            stop_count_incentive = payout.get_stopcount_pay()
            if any([payout.worked_hours, total_distance, total_qty]):
                holiday = plan.holiday_incentive_ids.filtered(
                    lambda
                        h: h.holiday_date == payout.date and total_qty >= h.min_no_of_order and payout.worked_hours >= h.min_no_of_hr
                )
                holiday_incentive = holiday[0].amount if holiday else 0.0

                if not holiday_incentive:
                    weekend_line = plan.weekend_incentive_ids.filtered(
                        lambda w: w.week_days == current_date.strftime('%a').lower()
                                  and w.min_hours <= payout.worked_hours and w.min_orders <= total_qty
                    )
                    weekend_incentive = weekend_line[0].amount if weekend_line else 0.0

        return {
            'total_distance': total_distance,
            'order_count': order_count,
            'total_revenue': total_revenue,
            'order_qty': total_qty,
            'stop_count_incentive': stop_count_incentive,
            'holiday_incentive': holiday_incentive,
            'weekend_incentive': weekend_incentive,
        }

    @api.model
    def check_daily_payout_fail(self):
        """
        Method is called by a cron task
        """
        # Fetch the first payout config record
        payout_config = self.env['driver.payout.date.config'].sudo().search([], limit=1)
        if payout_config:
            current_date = datetime.now().date()

            # Define the checks with corresponding failure reasons
            checks = [
                (payout_config.daily_trans_date, "Attendance Driver Daily Transaction"),
                (payout_config.so_daily_trans_date, "Sale order Driver Daily Transaction"),
            ]

            failed_dates = []
            failure_reasons = []

            # Check for discrepancies
            for trans_date, reason in checks:
                date_diff = (current_date - trans_date).days
                if date_diff != 1:
                    failed_dates.append((current_date - timedelta(days=(date_diff - 1))).isoformat())
                    failure_reasons.append(reason)

            # If failures are detected, prepare email context and send notification
            if failed_dates:
                failed_date_str = " and ".join(failed_dates)
                failure_reason_str = " and ".join(failure_reasons)

                ctx = {**self.env.context, 'reason': failure_reason_str, 'date': failed_date_str}

                # Fetch email template and send email
                template = self.env.ref('driver_management.driver_payout_fail_check_template', raise_if_not_found=False)
                if template:
                    template.with_context(ctx).send_mail(self.id, force_send=True)

    def get_email_groups(self):
        mail = []
        joined_string = ""
        approval_group = self.env.ref('driver_management.group_driver_payout_fail_check')
        if approval_group:
            for user in approval_group.users:
                mail.append(user.partner_id.email or '')
        if mail:
            joined_string = ",".join(mail)
        return joined_string

    def action_get_attendance(self):
        """
        Returns Driver attendance list view
        """
        attendance_ids = self.env['hr.attendance'].search(
            [('date', '=', self.date), ('employee_id', '=', self.employee_id.id)])
        context = dict(self._context)
        context.update({'driver_attendance': True})
        if attendance_ids:
            return {
                'name': _('Attendance'),
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'hr.attendance',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'context': context,
                'domain': [('id', 'in', attendance_ids.ids)],
            }

    def action_get_driver_so(self):
        """
        Returns Driver Sale order list view
        """
        start = datetime.combine(self.date, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
        end = (datetime.combine(self.date, datetime.min.time()) + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        start, end = self.convert_to_utc(start, end)

        so_ids = self.get_sale_orders(start, end, self.employee_id.id)
        view = self.env.ref('sale.view_quotation_tree_with_onboarding')
        context = dict(self._context)
        context.update({'daily_driver_so': True})
        if so_ids:
            return {
                'name': _('Quotations'),
                'view_type': 'form',
                'res_model': 'sale.order',
                'view_mode': 'tree',
                'view_id': view.id,
                'context': context,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', so_ids.ids)],
            }

    def unlink(self):
        """
        Prevent deletion of records linked with weekly/monthly payouts unless in specified states.
        """
        # Define states eligible for deletion
        allowed_states = ('draft', 'ready_verify', 'verify', 'approve',
                          'pending', 'complete_with_fail', 'complete')

        # Filter records in allowed states
        invalid_records = self.filtered(lambda r: r.status in allowed_states)

        # Raise validation error if any records are not in allowed states
        if invalid_records:
            raise ValidationError(
                _('You can only delete daily transactions not linked with weekly/monthly payouts.')
            )

        # Proceed with deletion
        return super(DriverPayout, self).unlink()
