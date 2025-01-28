# -*- coding: utf-8 -*-
from odoo import api, fields, models
from psycopg2.errors import UniqueViolation


class PayoutStatus(models.Model):

    _name = 'payout.status.update'
    _description = 'Payout Status Update'
    _rec_name = "batch_payout_id"


    is_check = fields.Boolean(string='Checked', default=False, index=True)
    batch_payout_id = fields.Many2one('driver.batch.payout',string="Payout Batch", index=True)

