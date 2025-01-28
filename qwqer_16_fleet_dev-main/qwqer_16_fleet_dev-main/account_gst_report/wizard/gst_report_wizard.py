from odoo import models, fields, api


class GSTReportWizard(models.TransientModel):
    _name = 'gst.report.wizard'

    def get_states(self):
        user = self.env.user
        user_country_id = user.company_id.country_id
        return [('country_id', '=', user_country_id.id)]

    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date', required=True)
    state_id = fields.Many2one('res.country.state', string='State')
    state_ids = fields.Many2many('res.country.state', 'gst_state_rel', 'gst_id', 'state_id', 'States',
                                 domain=get_states)
    service_type = fields.Many2one(comodel_name='partner.service.type', string="Service Type", domain=[('is_customer', '=', True)])

    def print_gstr1_xl_report(self):
        return self.env.ref('account_gst_report.gstr1_report_xl').report_action(self, data=self.read([])[0])

    def print_gstr2_xl_report(self):
        return self.env.ref('account_gst_report.gstr2_report_xl').report_action(self, data=self.read([])[0])
