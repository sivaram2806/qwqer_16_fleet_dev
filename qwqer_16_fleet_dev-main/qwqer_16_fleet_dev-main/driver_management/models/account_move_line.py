# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import datetime
import logging


_logger = logging.getLogger(__name__)


class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    driver_uid = fields.Char(string='Driver ID', index=True)
    driver_region_id = fields.Many2one(comodel_name='sales.region', string='Driver Region')

    def write(self, vals):
        res = super(AccountMoveLineInherit, self).write(vals)
        for rec in self:
            if rec.account_id.is_driver_account == True and rec.driver_uid:
                try:
                    driver_balance = self.env['application.driver.balance'].search(
                        [('driver_uid', '=', rec.driver_uid)], limit=1)
                    if not driver_balance:
                        driver_bal = {
                            'driver_uid': rec.driver_uid,
                            'time_balance_update': datetime.now(),
                        }
                        self.env['application.driver.balance'].create(driver_bal)
                except Exception as e:
                    _logger.exception("Error in Driver Balance Create/Update in Move line: %s", e)

            # # Update driver id for move lines
            # driver_id = rec.env['hr.employee'].search([('related_partner_id', '=', rec.partner_id.id)])
            # if driver_id:
            #     rec.driver_uid = driver_id.driver_uid
        return res