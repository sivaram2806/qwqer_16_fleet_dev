from odoo import api, exceptions, fields, models, _


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    salesperson_id = fields.Many2one('res.users', string='Sales Person', compute='_compute_salesperson_name',store=True)

    @api.depends('res_model', 'res_id', 'salesperson_id')
    def _compute_salesperson_name(self):
        for activity in self:
            if activity.res_model == 'crm.lead':
                activity.salesperson_id = activity.res_model and \
                                    self.env[activity.res_model].browse(activity.res_id).user_id or self.env.user

