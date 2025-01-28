# -*- coding: utf-8 -*-

import re
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class FleetVehicle(models.Model):
    """This model contains record of vehicle"""
    _name = 'vehicle.vehicle'
    _description = 'Vehicle'
    _inherit = 'mail.thread'
    _rec_name = 'vehicle_no'
    _order = 'vehicle_no asc'

    vehicle_no = fields.Char(string="Vehicle Number", required=True)
    vehicle_model_id = fields.Many2one(comodel_name="fleet.vehicle.model", string="Vehicle Model")
    vehicle_type_id = fields.Many2one(comodel_name="vehicle.vehicle.type", string="Vehicle Type")

    vehicle_pricing_lines = fields.One2many('vehicle.pricing.line', "vehicle_no", string='Vehicle Pricing',
                                            tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    def is_valid_vehicle_no(self, vehicle_no):
        # Remove any non-alphanumeric characters
        hyphen_pattern = r'(?<=\D)(?=\d)|(?<=\d)(?=\D)'
        cleaned_vehicle_no = re.sub(r'[^A-Za-z0-9]', '', vehicle_no.upper())
        with_hyphen = re.sub(hyphen_pattern, '-', cleaned_vehicle_no)
        if self.search([('vehicle_no', '=', with_hyphen)]):
            raise UserError(
                _("Vehicle with same vehicle number exists already !!!"))

        # Define the regular expression patterns
        pattern1 = r"^[A-Z]{2}(?!00)[0-9]{2}(?![OI])[A-HJ-NP-Z]{0,3}[0-9]{4}$"
        pattern2 = r"^(2[2-9]|[3-9][0-9])BH[0-9]{4}(?![OI])[A-HJ-NP-Z]{2,3}$"

        # Check if the cleaned_vehicle_no matches any of the patterns
        if re.match(pattern1, cleaned_vehicle_no) or re.match(pattern2, cleaned_vehicle_no):
            return True, with_hyphen, None
        else:
            # Determine the specific reason for failure
            if re.search(r'[OI]', cleaned_vehicle_no):
                return False, None, "contains 'O' or 'I'"
            elif not re.match(r'^[A-Z]{2}', cleaned_vehicle_no):
                return False, None, "should start with two alphabets"
            elif re.match(r'^[A-Z]{2}00', cleaned_vehicle_no):
                return False, None, "second part cannot be '00'"
            elif not re.match(r'^[A-Z]{2}[0-9]{2}', cleaned_vehicle_no):
                return False, None, "should have two digits after the initial alphabets"
            elif not re.match(r'^[A-Z]{2}[0-9]{2}(?![OI])[A-HJ-NP-Z]{1,3}', cleaned_vehicle_no):
                return False, None, "should have 1-3 alphabets after the digits"
            elif not re.match(r'^[A-Z]{2}[0-9]{2}(?![OI])[A-HJ-NP-Z]{1,3}[0-9]{4}$',
                              cleaned_vehicle_no) and not re.match(
                    r'^(2[2-9]|[3-9][0-9])BH[0-9]{4}(?![OI])[A-HJ-NP-Z]{2,3}$', cleaned_vehicle_no):
                return False, None, "should end with four digits"
            else:
                return False, None, "does not match any valid patterns"

    @api.model
    def create(self, vals_list):
        valid, cleaned_vehicle_no, message = self.is_valid_vehicle_no(vals_list.get('vehicle_no'))
        if valid:
            vals_list['vehicle_no'] = cleaned_vehicle_no
            return super().create(vals_list)
        else:
            raise UserError(
                _("INVALID VEHICLE NUMBER!!! \n\nVehicle number '%s' %s" % (vals_list['vehicle_no'], message)))
