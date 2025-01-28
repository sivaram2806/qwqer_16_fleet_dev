# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ContractAttachments(models.Model):
    """
    This model contains all the attachments of contract, #V13_model name:  agreement.attachment
    """
    _name = "contract.attachments"
    _description = "Contract Attachments"

    contract_agreement = fields.Char(string='Attachment File name')
    attachment = fields.Binary(string='Attachment') #V13_field: agrmnt_attmnt
    note = fields.Char(string="Description") #V13_field: description
    contract_id = fields.Many2one(comodel_name='vehicle.contract',
                                  string='Contract ID') #V13_field: contract_management_id, model: 'contract.management'
