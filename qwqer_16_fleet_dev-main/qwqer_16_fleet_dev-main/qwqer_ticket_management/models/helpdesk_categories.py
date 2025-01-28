from odoo import fields, models


class HelpdeskCategories(models.Model):
    """This class represents the Helpdesk Categories, providing information
    about different categories that can be assigned to helpdesk items.
   """
    _name = 'helpdesk.categories'
    _description = 'Helpdesk Categories'

    name = fields.Char(string='Name', help='Category Name')
    sequence = fields.Integer(string='Sequence', default=0,
                              help='Sequence of a Category')
