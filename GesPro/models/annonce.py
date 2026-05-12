from odoo import models, fields, api


class Annonce(models.Model):
    _name = 'gespro.annonce'
    _description = 'Annonce '
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_en desc'

    name = fields.Char(string="Reference", required=True, copy=False, readonly=True, default=lambda self: ('New'))
    capture = fields.Binary(string="capture d'ecran")
    capture_name = fields.Char(string="capture d'ecran name")
    file = fields.Binary(string="Fichier")
    file_name = fields.Char(string="Nom du fichier")
    user_id= fields.Many2one('res.users', string='Auteur', default=lambda self: self.env.user)
    state = fields.Selection([
        ('read', 'Lu'),
        ('notRead', 'Non lu'),
    ], string='Status', default='notRead')
    description = fields.Text(string='Description')
    date_envoi = fields.Date(string='Date Posted', default=fields.Date.today)
    note_refus = fields.Text(string='Motif de refus')

    