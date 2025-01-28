from . import models
from odoo import api, SUPERUSER_ID
from . import report

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['crm.stage'].hide_default_proposition_stage()