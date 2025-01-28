from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    customer_update_log_ids = fields.One2many(comodel_name='customer.update.log', inverse_name='partner_id')
    pricing_plan_update_log_ids = fields.One2many(comodel_name='pricing.plan.update.log', inverse_name='partner_id')
    additional_charge_update_log_ids = fields.One2many(comodel_name='additional.charge.update.log',inverse_name= 'partner_id')


class SlabPricePlanUpdateLog(models.Model):
    _name = 'pricing.plan.update.log'

    minimum_weight = fields.Float(string="From Weight(Kg)")
    maximum_weight = fields.Float(string="To Weight(Kg)")
    from_distance = fields.Float(string="From Distance(Km)")
    to_distance = fields.Float(string="To Distance(Km)")
    min_distance = fields.Float(string="Minimum Distance(Km)")
    min_cost = fields.Float(string="Minimum Cost(Rs)")
    per_km_charge = fields.Float(string="Per Kilometre Charge(Rs)")
    price = fields.Float(string="Price(Rs)")
    updated_by = fields.Many2one(comodel_name='res.users',string='Updated By')
    updated_date_time = fields.Datetime("Updated Time")
    select_plan_type = fields.Selection(selection=[('KM', 'KM'),
                                      ('slab', 'SLAB'),
                                      ('flat', 'FLAT')],
                                     string="Pricing Model", default='KM', copy=False)
    partner_id = fields.Many2one('res.partner')
    action = fields.Char(string="Action")
    
    
class AdditionalChargeUpdateLog(models.Model):
    _name = 'additional.charge.update.log'

    charge_type_id = fields.Many2one('charge.type', string="Charge Type")
    amount_type = fields.Selection([('percentage', 'Percentage'),
                                     ('flat', 'Flat')],
                                            string="Amount Type")
    amount = fields.Float('Amount/Percentage')
    updated_by = fields.Many2one('res.users', "")
    updated_date_time = fields.Datetime("Updated Time")
    partner_id = fields.Many2one('res.partner')
    action = fields.Char(string="Action")


class CustomerUpdateLog(models.Model):
    _name = 'customer.update.log'

    partner_id = fields.Many2one('res.partner')
    created_by = fields.Many2one('res.users', string='Updated By')
    date_time = fields.Datetime("Updated Time")
    change_request_id = fields.Many2one('customer.master.change.request', string='Change Request No')

    def open_change_request(self):
        # view_id = self.env.ref('qw_customer_master_chng_req.customer_master_change_request_form').id
        return {
            'name': _('Change Request '),
            'view_type': 'form',
            'target': 'new',
            "view_mode": 'form',
            'res_model': 'customer.master.change.request',
            'res_id': self.change_request_id.id,
            'type': 'ir.actions.act_window',
        }
