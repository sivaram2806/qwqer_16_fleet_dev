from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    category_type = fields.Selection(string='Type',
                                     selection=[('travel', 'Travel'),
                                                ('lodging', 'Lodging'), ('boarding', 'Boarding'),
                                                ('other', 'Other'), ])

    @api.constrains('category_type')
    def _check_unique_category_type(self):
        """ This constraint ensures there is only one product with each of the selected types. """
        for record in self:
            if record.category_type in ['travel', 'lodging', 'boarding']:
                other_records = self.search([('category_type', '=', record.category_type), ('id', '!=', record.id)])
                if other_records:
                    raise ValidationError(
                        "A product with the category type '%s' already exists. Only one is allowed." % dict(
                            self._fields['category_type'].selection).get(record.category_type)
                    )
