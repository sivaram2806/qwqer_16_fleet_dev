from odoo import fields, models, _
from lxml import etree


class FTLTrackingHistory(models.Model):
    _name = "ftl.track.history"
    _rec_name = 'ftl_trip_id'
    _description = "FTL Tracking History"
    _order = 'location_sequence'

    location_sequence = fields.Integer(string="Sequence")
    latitude = fields.Float(string='Latitude', digits=(10, 7), store=True)
    longitude = fields.Float(string='Longitude', digits=(10, 7), store=True)
    time_recorded = fields.Datetime(string="Time Stamp", store=True)
    location = fields.Char(string="Location", store=True)
    ftl_trip_id = fields.Many2one('batch.trip.ftl', store=True)
    track_trip_status = fields.Char(related='ftl_trip_id.track_trip_status', string="Status", store=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company, store=True)
    user_id = fields.Many2one('res.users', 'Created BY', default=lambda self: self.env.user, store=True)
