from odoo import models, fields

class CEOResponse(models.Model):
    _name = 'gespro.reponse_ceo'
    _description = 'CEO Response'

    name = fields.Char(string='Response Reference', required=True, copy=False, readonly=True, default=lambda self: ('Nouveau')) 
    capture = fields.Binary(string="Capture d'écran", required=True)
    capture_name = fields.Char(string="Nom de la capture d'écran", required=True)
    description= fields.Text(string='Description', required=True)
    user_id= fields.Many2one('res.users', string='Auteur', default=lambda self: self.env.user, readonly=True)
    date_envoi = fields.Datetime(string='Date of Response', default=fields.Datetime.now, readonly=True)
    state = fields.Selection([('lu', 'Lu'), ('non_lu', 'Non lu')], string='Status', default='non_lu')
    annonce_id = fields.Many2one('gespro.annonce', string='Annonce', required=True, ondelete='cascade')