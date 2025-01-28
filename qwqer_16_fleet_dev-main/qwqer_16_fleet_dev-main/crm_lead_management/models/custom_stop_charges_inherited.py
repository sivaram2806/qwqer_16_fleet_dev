from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CustomerStopCharge(models.Model):
    _inherit = "customer.additional.charges"
    _description = "Customer Additional Charges"

    crm_id = fields.Many2one('crm.lead', string="CRM")

    @api.model
    def create(self, values):
        res = super(CustomerStopCharge, self).create(values)
        if values.get('crm_id') and  self.env.context.get('crm_lead_form',False):
            result = self.search([('crm_id', '=', res.crm_id.id),('charge_type_id', '=', res.charge_type_id.id)])
            if result and  len(result) >1:
                raise UserError(_("In the additional charges section, the same charge type %s are added multiple times.Please remove the duplicates.")% (res.charge_type_id.name))
        return res

    def write(self, values):
        res = super(CustomerStopCharge, self).write(values)
        if values.get('charge_type_id') and  self.env.context.get('crm_lead_form',False):
            result = self.search([('crm_id', '=', self.crm_id.id),('charge_type_id', '=', self.charge_type_id.id)])
            if result and  len(result) >1:
                raise UserError(_("In the additional charges section, the same charge type %s are added multiple times.Please remove the duplicates.")% (self.charge_type_id.name))
        return res
