# -*- coding: utf-8 -*-
import base64

from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Bank Details
    apply_tds = fields.Boolean(string = "TDS Applicable")
    is_under_vendor = fields.Boolean(string='Payment To Vendor', default=False)  # V13_field: driver_partner
    pan_no = fields.Char(string="PAN No")
    account_no = fields.Char(string='Account Number', copy=False)
    ifsc_code = fields.Char(string='IFSC Code', copy=False)
    upi_id = fields.Char(string='UPI ID')
    beneficiary_uid = fields.Char(string="Beneficiary ID", copy=False)  # V13_field: beneficiary_uid
