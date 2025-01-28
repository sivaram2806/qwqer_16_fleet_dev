from email.policy import default

from odoo import models, api, fields, _

class HidePropositionStage(models.Model):
    _inherit = 'crm.stage'


    is_lost = fields.Boolean('Is Lost Stage?')
    is_qualified = fields.Boolean('Is qualified ?')

    @api.model
    def hide_default_proposition_stage(self):
        stage = self.search([('name', '=', 'Proposition')], limit=1)
        if stage:
            stage.unlink()
