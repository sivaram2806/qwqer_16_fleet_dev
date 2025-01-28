from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CustomerAdditionalCharge(models.Model):
    _name = "customer.additional.charges"
    _description = "Customer Additional Charges"

    charge_type_id = fields.Many2one('charge.type', string="Charge Type", store=True)
    amount_type = fields.Selection([('percentage', 'Percentage'),
                                     ('flat', 'Flat')], string="Amount Type")
    amount = fields.Float('Amount/Percentage')
    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer")
    crm_id = fields.Many2one('crm.lead', string="CRM")

    """ To Avoid the duplication of charge type while creating crm leads and edit the form"""

    @api.constrains('charge_type_id')
    def _check_charge_type_unique(self):
        for rec in self:
            if rec.crm_id and rec.charge_type_id:
                result = self.env['customer.additional.charges'].search([('crm_id', '=', rec.crm_id.id),
                                                                   ('charge_type_id', '=', rec.charge_type_id.id)])
                if result and len(result) > 1:
                    raise UserError(_("In the additional charges section, "
                                      "the same charge type %s are added multiple times. Please remove the duplicates.")
                                        % ( rec.charge_type_id.name))
