from odoo import models, fields, api, _
from datetime import datetime,timedelta
from odoo.exceptions import ValidationError
import requests
import json
import logging

_logger = logging.getLogger(__name__)



class ApplicationDriverBalance(models.Model):
    _name = 'application.driver.balance'
    _rec_name = "driver_uid"
    _description = 'Application driver balance'
    _order= 'id,time_balance_update desc'


    partner_id = fields.Many2one('res.partner', string='Partner')
    driver_uid = fields.Char("Driver ID", index=True)
    time_balance_update = fields.Datetime("Time of Balance Update")
    balance = fields.Float("Balance", digits='Product Price')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.company)


    def action_for_update_driver_balance(self):
        auth_token = self.company_id.driver_balance_token
        record_limit = self.company_id.driver_balance_limit
        driver_balance_url = self.company_id.driver_balance_url
        if not all([auth_token, record_limit, driver_balance_url]):
            raise ValidationError(_("Driver balance configuration is missing."))
        vals_data = self
        if not vals_data or len(vals_data) > record_limit:
            raise ValidationError(_("Selected Record should be less than %s")%str(record_limit))
        today_date = datetime.now().date()
        start = datetime.combine(today_date, datetime.min.time())
        end = start + timedelta(days=1)
        driver_ids = vals_data.mapped('driver_uid')
        if driver_ids:
            driver_balance = self.get_driver_closing_balance(driver_ids,end.date())
            if driver_balance:
                payload = {"params": []}
                headers = {
                    'Authorization': auth_token,
                    'content-type': "application/json",
                }
                for line in driver_balance:
                    # Get the most recent record for the driver
                    record_ids = vals_data.filtered(lambda d: d.driver_uid == line['driver_uid'])
                    if len(record_ids) > 1:
                        sort_record_ids = sorted(record_ids, key=lambda k: k.id, reverse=True)
                        rec_id = sort_record_ids[0]
                    else:
                        rec_id = record_ids
                    payload['params'].append({
                        "rider_id": int(line['driver_uid']),
                        "cash_in_hand": line['balance'],
                        "last_updated_at": rec_id and rec_id.time_balance_update and str(
                            rec_id.time_balance_update) or str(datetime.now())
                    })
                try:
                    response = requests.request("POST",driver_balance_url,json=payload, headers=headers)
                    dms_response = json.loads(response.text)
                    response_data = response.json()
                    if dms_response:
                        if dms_response['status'] == 200:
                            _logger.info("Success :Driver Balance Api from Server response:%s", str(dms_response))
                            success_driver_ids = response_data.get('data', {}).get('success', [])
                            if success_driver_ids:
                                unlink_data = vals_data.filtered(lambda m: int(m.driver_uid) in success_driver_ids)
                                if unlink_data:
                                    if len(unlink_data) == 1:
                                        self.env.cr.execute(
                                            """DELETE FROM application_driver_balance WHERE id = %s;""" % str(
                                                unlink_data.id))
                                    else:
                                        self.env.cr.execute(
                                            """DELETE FROM application_driver_balance WHERE id in %s;""" % (
                                            tuple(unlink_data.ids),))
                        else:
                            _logger.info("Error : Occur in driver balance api scheduler.Response:%s", str(dms_response))
                except Exception as e:
                    _logger.info("Error : Occur in driver balance api scheduler")


    @api.model
    def get_driver_balance(self):
        """ Update the driver balance to dms by using scheduler """
        auth_token = self.env.company.driver_balance_token
        record_limit = self.env.company.driver_balance_limit
        driver_balance_url = self.env.company.driver_balance_url
        if auth_token and driver_balance_url and record_limit:
            vals_data = self.env['application.driver.balance'].search([], limit=record_limit)
            if vals_data:
                vals_data.action_for_update_driver_balance()

    def get_driver_closing_balance(self, driver_ids, end_date):
        if not driver_ids or not end_date:
            return []

        # Query to find sum of closing balance

        sql = """
                SELECT 
                    SUM(balance) as balance, driver_uid 
                FROM 
                    account_move_line 
                WHERE 
                    driver_uid IN %s
                    AND date <= %s 
                    AND account_id IS NOT NULL 
                    AND account_id IN (
                        SELECT id FROM account_account WHERE is_driver_account = TRUE
                    ) 
                    AND parent_state = 'posted' 
                    AND partner_id IS NOT NULL
                GROUP BY 
                    driver_uid
            """
        params = (tuple(driver_ids), end_date)
        self.env.cr.execute(sql, params)
        b_sum = self.env.cr.dictfetchall()
        return b_sum
