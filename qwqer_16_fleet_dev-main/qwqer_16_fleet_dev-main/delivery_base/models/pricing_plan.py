from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PricingPlan(models.Model):
    _name = "pricing.plan"
    _description = "Select Pricing Plan For Lead"

    minimum_weight = fields.Float(string="From Weight(Kg)")
    maximum_weight = fields.Float(string="To Weight(Kg)")
    min_distance = fields.Float(string="Minimum Distance(Km)")
    min_cost = fields.Float(string="Minimum Cost(Rs)")
    per_km_charge = fields.Float(string="Per Kilometre Charge(Rs)")
    select_plan_type = fields.Selection([('KM', 'Kilometer'),
                                         ('slab', 'Slab'),
                                         ('flat', 'Flat')],
                                        string="Select Plan",store=1)
    from_distance = fields.Float(string="From Distance(Km)")
    to_distance = fields.Float(string="To Distance(Km)")
    price = fields.Float(string="Price(Rs)")
    partner_id = fields.Many2one(comodel_name='res.partner',string='Partner Id')

    @api.constrains('minimum_weight', 'maximum_weight', 'min_distance', 'min_cost', 'per_km_charge')
    def plan_validation(self):
        for rec in self:
            if rec.select_plan_type == 'KM':
                if (rec.minimum_weight == 0.00 and rec.maximum_weight == 0.00 and rec.min_distance == 0.00 and
                        rec.min_cost == 0.00 and rec.per_km_charge == 0.00):
                    raise ValidationError(_('KM Pricing plan cannot be created without any price data '))

            if rec.select_plan_type == 'slab':
                if (rec.minimum_weight == 0.00 and rec.maximum_weight == 0.00 and rec.from_distance == 0.00 and
                        rec.to_distance == 0.00 and rec.price == 0.00):
                    raise ValidationError(_('Slab Pricing plan cannot be created without any price data '))

            if rec.select_plan_type == 'flat':
                if (rec.minimum_weight == 0.00 and rec.maximum_weight == 0.00 and rec.price == 0.00):
                    raise ValidationError(_('Flat Pricing plan cannot be created without any price data '))