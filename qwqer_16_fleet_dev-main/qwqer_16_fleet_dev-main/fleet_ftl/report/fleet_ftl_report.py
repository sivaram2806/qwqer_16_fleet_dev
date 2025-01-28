# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID

from functools import lru_cache


class BatchTripStatistics(models.Model):
    _name = "batch.trip.ftl.report"
    _description = "Batch Trip Statistics"
    _auto = True
    _rec_name = 'trip_date'
    _order = 'trip_date desc'

    # ==== Invoice fields ====
    name = fields.Char(string='Trip Number')
    trip_date = fields.Date(string='Trip Date')
    customer_id = fields.Many2one(comodel_name='res.partner', string='Customer')
    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor')
    region_id = fields.Many2one(comodel_name='sales.region', string='Region')
    comments = fields.Text()
    invoice_state = fields.Selection([
        ("to_invoice", "To Invoice"),
        ("invoiced", "Invoiced"),
        ("nothing_to_invoice", "Nothing to Invoice")], string='Invoice Status',
        default="to_invoice", copy=False, index=True, tracking=True)
    state = fields.Selection([
        ("new", "New"),
        ("pending_approval", "Pending Approval"),
        ("ops_approved", "Ops Approved"),
        ("finance_approved", "Finance Approved"),
        ("completed", "Completed"),
        ("rejected", "Rejected")], default="new", copy=False, tracking=True)
    is_invoice_paid = fields.Boolean(string='Invoice Paid')
    trip_type = fields.Selection([('fleet_urban_haul', 'Fleet Urban Haul'), ('fleet_ftl', 'Fleet FTL')])
    work_order_id = fields.Many2one(comodel_name='work.order', string='Work Order')
    work_order_amount = fields.Monetary(string='Work Order Amount', related='work_order_id.total_amount')
    work_order_shipping_address = fields.Text(string='Work Order Shipping Address',
                                              related='work_order_id.shipping_address')
    currency_id = fields.Many2one(comodel_name='res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id)
    lorry_receipt_no=fields.Char(string='Lorry Receipt No')
    ftl_batch_trip_id = fields.Many2one(comodel_name='batch.trip.ftl', string="Ftl Daily Trip", readonly=True, copy=True)
    eway_bill_number = fields.Char(string='Eway Bill Number')
    total_trip_amount = fields.Float(string='Total Trip Amount', compute='_compute_total_trip_amount', store=True)
    trip_summary_ftl_id = fields.Many2one(comodel_name='trip.summary.ftl', ondelete='cascade', index=True, copy=False)
    vehicle_id = fields.Many2one(string='Vehicle Number', comodel_name='vehicle.vehicle')
    vehicle_model_id = fields.Many2one(string='Vehicle Model', comodel_name='fleet.vehicle.model',
                                       related='vehicle_id.vehicle_model_id')
    vehicle_type_id = fields.Many2one(string='Vehicle Type', related='vehicle_id.vehicle_type_id')
    vehicle_description = fields.Char(string='Vehicle Description')
    package_description = fields.Char(string='Package Description')
    start_date = fields.Date(string='Start date', required=True)
    end_date = fields.Date(string='End date', required=True)
    total_km = fields.Float(string='Total KM')
    # quantity = fields.Integer(string='Qty', default=1)
    tonnage = fields.Integer(string='Tonnage', default=1)
    company_id = fields.Many2one(comodel_name='res.company', string="Company", required=True, readonly=True,
                                 default=lambda self: self.env.company)
    source_id = fields.Many2one("res.state.city")
    destination_id = fields.Many2one("res.state.city")

    vendor_advance_paid = fields.Float(string='Vendor Adv. Paid', digits='Product Price',
                                  )
    bill_amount = fields.Float(string='Bill Amount', digits='Product Price')

    invoice_amount = fields.Float(digits='Product Price', )
    amount_payable = fields.Float(digits='Product Price', )
    amount_receivable = fields.Float(digits='Product Price', )
    # _depends = {
    #     'batch.trip.ftl': [
    #         'name', 'trip_date', 'customer_id', 'vendor_id', 'region_id', 'comments',
    #         'invoice_state', 'state', 'is_invoice_paid',
    #         'trip_type', 'work_order_id', 'work_order_amount', 'work_order_shipping_address',
    #         'lorry_receipt_no', 'pod_attachment', 'pod_attachment_name', 'vehicle_id', 'vehicle_model_id',
    #         'vehicle_type_id', 'vehicle_description', 'package_description', 'start_date', 'end_date', 'total_km',
    #         'quantity', 'tonnage', 'source_id', 'destination_id'
    #     ],
    # }

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    args.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    args.append(('region_id', 'in', []))
        res = super(BatchTripStatistics, self).search(args, offset, limit, order, count=count)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.id != SUPERUSER_ID:
            if self.env.user.has_group('qwqer_base.region_filter_group'):
                if self.env.user.displayed_regions_ids:
                    domain.append(('region_id', 'in', self.env.user.displayed_regions_ids.ids))
                else:
                    domain.append(('region_id', 'in', []))
        return super(BatchTripStatistics, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)

    @property
    def _table_query(self):
        return '%s %s %s %s' % (self._select(), self._from(), self._where(), self._group_by())

    @api.model
    def _select(self):
        return '''
            SELECT
                btf.id as ftl_batch_trip_id,
                btf.id,
                btf.vehicle_id,
                btf.vehicle_model_id,
                btf.vehicle_type_id,
                btf.vehicle_description,
                btf.package_description,
                btf.start_date,
                btf.end_date,
                btf.total_km,
                btf.tonnage,
                btf.source_id,
                btf.destination_id,
                btf.name,
                btf.trip_date,
                btf.customer_id,
                btf.vendor_id,
                btf.region_id,
                btf.comments,
                btf.invoice_state,
                btf.state,
                btf.currency_id,
                btf.company_id,
                btf.is_invoice_paid,
                btf.trip_type,
                btf.work_order_id,
                btf.work_order_amount,
                btf.work_order_shipping_address,
                btf.lorry_receipt_no,
                btf.eway_bill_number,
                btf.total_trip_amount,
                btf.trip_summary_ftl_id,
                btf.amount_alert_bool,
                wo.vendor_advance_paid,
                wo.bill_amount,
                wo.invoice_amount,
                wo.amount_payable,
                wo.amount_receivable
        '''

    @api.model
    def _from(self):
        return '''
            FROM batch_trip_ftl btf
                LEFT OUTER JOIN res_partner customer ON customer.id = btf.customer_id
                LEFT OUTER JOIN res_partner vendor ON vendor.id = btf.vendor_id
                LEFT OUTER JOIN work_order wo ON wo.id = btf.work_order_id
        '''

    @api.model
    def _where(self):
        return '''where btf.company_id = %s'''% self.env.company.id

    def _group_by(self):
        group_by_str = """
               GROUP BY
                   btf.vehicle_id,
                   btf.vehicle_model_id,
                   btf.vehicle_type_id,
                   btf.vehicle_description,
                   btf.package_description,
                   btf.source_id,
                   btf.destination_id,
                   btf.name,
                   btf.trip_date,
                   btf.customer_id,
                   btf.vendor_id,
                   btf.region_id,
                   btf.state,
                   btf.company_id,
                   btf.work_order_id,
                   wo.vendor_advance_paid,
                   btf.id,
                   wo.bill_amount,
                   wo.invoice_amount,
                   wo.amount_payable,
                   wo.amount_receivable
           """
        return group_by_str