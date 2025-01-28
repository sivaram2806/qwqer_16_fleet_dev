from odoo import models, fields


class InheritSaleOrderLines(models.Model):
    _inherit = 'sale.order.line'

    service_type_id = fields.Many2one(comodel_name='partner.service.type')

    def _prepare_invoice_line(self, **optional_values):
        res = super(InheritSaleOrderLines, self)._prepare_invoice_line(**optional_values)
        res.update({'service_type_id': self.service_type_id.id})
        return res
