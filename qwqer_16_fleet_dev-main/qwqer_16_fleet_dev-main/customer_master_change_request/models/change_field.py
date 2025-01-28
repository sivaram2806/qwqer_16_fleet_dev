# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class CustomerMasterChangeField(models.Model):
    """ model for collecting the filed to change"""
    _name = 'change.field'

    name = fields.Char('Field')
    code = fields.Char('Code')
    is_credit_payment = fields.Boolean("Is a Credit Payment Mode")
    is_fleet_service_field = fields.Boolean(string='Is Fleet Service Field',
                                            help="Field only for fleet service")
    is_ftl_service_field = fields.Boolean(string='Is FTL Fleet Service Field',
                                          help="Field only for FTL fleet service")
    is_delivery_service_field = fields.Boolean(string='Is Delivery/Qshop Service Field',
                                               help="Field only for delivery/qshop service")
