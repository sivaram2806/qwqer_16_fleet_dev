from odoo import fields, models, api, _


class Payments(models.Model):
    _inherit = "account.payment"

    sales_person_id = fields.Many2one('hr.employee', string='Sales Person')
    region_id = fields.Many2one('sales.region', string='Region')

    @api.onchange('partner_id')
    def onchange_customer(self):
        if self.partner_id:
            self.sales_person_id = self.partner_id.order_sales_person.id if self.partner_id.order_sales_person else False
            self.region_id = self.partner_id.region_id.id if self.partner_id.region_id else False

    def action_post(self):
        res = super(Payments, self).action_post()
        for rec in self:
            if rec.sales_person_id and rec.region_id:
                sales_person_collection = self.env['salesperson.target.list'].search(
                    [('sales_person_id', '=', rec.sales_person_id.id),
                     ('from_date', '<=', rec.date),
                     ('to_date', '>=', rec.date),
                     ('region_id', '=', rec.region_id.id)])
                if sales_person_collection:
                    for collection in sales_person_collection:
                        collection._compute_sales_person_wise_total_achieved_revenue()
        return res





