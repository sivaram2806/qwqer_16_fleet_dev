# -*- coding: utf-8 -*-

from odoo import models, fields, api

from functools import lru_cache

TRIP_STATE = [
    ("new", "New"),
    ("pending_approval", "Pending Approval"),
    ("approved", "Approved"),
    ("completed", "Completed"),
    ("rejected", "Rejected")
]

INVOICE_STATE = [
    ("to_invoice", "To Invoice"),
    ("invoiced", "Invoiced"),
    ("nothing_to_invoice", "Nothing to Invoice")
]

FREQUENCY = [
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
]

CALCULATION_FREQUENCY = [
    ("daily", "Daily"),
    ("monthly", "Monthly"),
]

BILL_STATE = [
    ("to_paid", "To Be Paid"),
    ("paid", "Billed"),
    ("nothing_to_paid", "Nothing to Bill")
]

class BatchTripUHStatistics(models.Model):
    _name = "batch.trip.uh.report"
    _description = "Batch Trip Statistics"
    _auto = True
    _rec_name = 'trip_date'
    _order = 'trip_date desc'

    state = fields.Selection(TRIP_STATE, default=TRIP_STATE[0][0], copy=False, index=True, tracking=True)
    name = fields.Char()
    customer_id = fields.Many2one('res.partner')
    trip_date = fields.Date()
    invoice_state = fields.Selection(INVOICE_STATE, string='Invoice Status', default=INVOICE_STATE[0][0],
                                     copy=False, index=True, tracking=True)
    region_id = fields.Many2one('sales.region', string='Trip Region')
    frequency = fields.Selection(FREQUENCY, default=FREQUENCY[0][0], string="Frequency", copy=False)
    comments = fields.Text()
    sales_person_id = fields.Many2one('hr.employee', string='Sales Person')

    # Other Info
    mail_approval_received = fields.Selection([
        ("yes", "Yes"),
        ("no", "No")], default="no", string='Mail Approval Received?')

    approved_user_id = fields.Many2one('res.users', string='Approved User')
    # Other fields
    edit_bool = fields.Boolean(string='Edit Bool', default=True, copy=False)
    is_invoice_paid = fields.Boolean(string='Invoice Paid', store=True)
    vendor_total_amount = fields.Float(string='Vendor Total Amount', digits='Product Price')
    customer_total_amount = fields.Float(string='Customer Total Amount', digits='Product Price')
    # Vendor Daily Trip form view differentiate field
    is_vendor_trip = fields.Boolean(string='Vendor Trip?', default=False, copy=False)
    trip_no = fields.Char()
    vehicle_pricing_line_id = fields.Many2one('vehicle.pricing.line')
    vehicle_model_id = fields.Many2one('fleet.vehicle.model')
    vehicle_pricing_id = fields.Many2one('vehicle.pricing', string='Vehicle Pricing', store=True)
    vehicle_description = fields.Char(string='Vehicle Description')
    vendor_id = fields.Many2one('res.partner')
    bill_state = fields.Selection(BILL_STATE, string='Bill Status', default=BILL_STATE[0][0], copy=False, index=True)
    start_time = fields.Float(default=9.0)
    end_time = fields.Float(default=18.0)
    total_time = fields.Float(store=True)
    start_km = fields.Float(string="Start Odo")
    end_km = fields.Float(string="End Odo")
    total_km = fields.Float(string="Total Odo", store=True)
    customer_km_cost = fields.Float(digits='Product Price')
    customer_hour_cost = fields.Float(digits='Product Price')
    vendor_km_cost = fields.Float(digits='Product Price')
    vendor_hour_cost = fields.Float(digits='Product Price')
    customer_amount = fields.Float(digits='Product Price',  store=True)
    vendor_amount = fields.Float(digits='Product Price', store=True)
    calculation_frequency = fields.Selection(CALCULATION_FREQUENCY, default=CALCULATION_FREQUENCY[0][0],
                                             string="Customer Calculation Method", store=True)

    vendor_calculation_frequency = fields.Selection(CALCULATION_FREQUENCY, default=CALCULATION_FREQUENCY[0][0],
                                                    string=" Vendor Calculation Method",store=True)
    driver_name = fields.Char()
    cumulative_vendor_amount = fields.Float(digits='Product Price', string='Cumulative Vendor Amount')
    cumulative_customer_amount = fields.Float(digits='Product Price', string='Cumulative Customer Amount')
    batch_trip_uh_id = fields.Many2one('batch.trip.uh', string="Daily Trip", ondelete='cascade', index=True, copy=True)
    trip_summary_customer_id = fields.Many2one('trip.summary.uh', string='Trip Summary Customer', index=True)
    trip_summary_vendor_id = fields.Many2one('trip.summary.uh', string='Trip Summary Vendor', index=True)
    # Company id for Multi-Company property
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    _depends = {
        'batch.trip.uh': [
            'state', 'name', 'customer_id', 'trip_date', 'invoice_state', 'region_id', 'frequency', 'comments',
            'sales_person_id', 'attachment_ids', 'mail_approval_received', 'approved_user_id', 'is_invoice_paid',
            'vendor_total_amount', 'customer_total_amount', 'is_vendor_trip' ],
        'batch.trip.uh.line': [
            'trip_no',  'vendor_id',
            'bill_state', 'start_time', 'end_time', 'total_time',
            'start_km', 'end_km', 'total_km', 'customer_km_cost', 'customer_hour_cost', 'vendor_km_cost', 
            'vendor_hour_cost', 'customer_amount', 'vendor_amount', 'vendor_id',
            'calculation_frequency', 'vendor_calculation_frequency', 'driver_name', 'cumulative_vendor_amount',
            'cumulative_customer_amount', 'batch_trip_uh_id', 'trip_summary_customer_id', 'trip_summary_vendor_id',
            "company_id"
        ],
    }

    @property
    def _table_query(self):
        return '%s %s %s' % (self._select(), self._from(), self._where())

    @api.model
    def _select(self):
        return '''
            SELECT
                line.id,
                line.trip_no,
                line.vendor_id,
                line.bill_state,
                line.start_time,
                line.end_time,
                line.total_time,
                line.start_km,
                line.end_km,
                line.total_km,
                line.customer_km_cost,
                line.customer_hour_cost,
                line.vendor_km_cost,
                line.vendor_hour_cost,
                line.customer_amount,
                line.vendor_amount,
                line.calculation_frequency,
                line.vendor_calculation_frequency,
                line.driver_name,
                line.cumulative_vendor_amount,
                line.cumulative_customer_amount,
                line.batch_trip_uh_id,
                line.trip_summary_customer_id,
                line.trip_summary_vendor_id,
                btu.state,
                btu.name,
                btu.customer_id,
                btu.trip_date,
                btu.invoice_state,
                btu.region_id,
                btu.frequency,
                btu.comments,
                btu.sales_person_id,
                btu.mail_approval_received,
                btu.approved_user_id,
                btu.is_invoice_paid,
                btu.vendor_total_amount,
                btu.customer_total_amount,
                btu.is_vendor_trip
        '''

    @api.model
    def _from(self):
        return '''
            FROM batch_trip_uh_line line
                INNER JOIN batch_trip_uh btu ON btu.id = line.batch_trip_uh_id
                LEFT OUTER JOIN res_partner customer ON customer.id = btu.customer_id
                LEFT OUTER JOIN res_partner vendor ON vendor.id = line.vendor_id
        '''

    @api.model
    def _where(self):
        return '''where btu.company_id = %s'''% self.env.company.id