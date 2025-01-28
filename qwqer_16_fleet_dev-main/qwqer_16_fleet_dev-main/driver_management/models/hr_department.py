# -*- coding: utf-8 -*-

from odoo import models, fields


class SalesRegion(models.Model):
    _inherit = 'sales.region'

    department_id = fields.Many2one('hr.department',string='Department')
    default_driver_payout_plan = fields.Many2one('driver.payout.plans', string='Default Driver Payout Plan')

from odoo import models, fields, api, _

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    region_ids = fields.One2many('sales.region','department_id',string='Regions')