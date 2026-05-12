from odoo import models, fields

class CEOResponse(models.Model):
    _name = 'gespro.ceo.response'
    _description = 'CEO Response'

    annonce_id = fields.Many2one('gespro.annonce', string='Annonce', required=True)
    response_text = fields.Text(string='Response Text')
    date_response = fields.Date(string='Date of Response', default=fields.Date.today)