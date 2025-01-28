# -*- coding: utf-8 -*-
from odoo import models, fields


class StateJournal(models.Model):
    _name = 'state.journal'
    _description = 'State Journal'
    _rec_name = 'fleet_journal_id'

    def get_states(self):
        """domain setting function for the state_id field
            @return [country_id]
        """
        user = self.env.user
        user_country_id = user.company_id.country_id
        return [('country_id', '=', user_country_id.id)]

    state_id = fields.Many2one("res.country.state", string='State', domain=get_states)
    fleet_journal_id = fields.Many2one("account.journal", string='Fleet Invoice Journal')
    vendor_bill_journal_id = fields.Many2one("account.journal", string='Fleet Bill Journal')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

