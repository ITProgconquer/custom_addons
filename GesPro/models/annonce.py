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
        ('new', 'Nouveau'),
        ('lu', 'Lu'),
        ('non_lu', 'Non lu')
    ], string='Status', default='new', tracking=True)
    description = fields.Text(string='Description')
    date_envoi = fields.Date(string='Date Posted', default=fields.Date.today)
    note_refus = fields.Text(string='Motif de refus')
    appel_id = fields.One2many('gespro.appel', 'annonce_id', string='Appel d\'offre')
    reponse_ceo_ids = fields.One2many('gespro.ceo.response', 'annonce_id', string='Réponses du CEO')

    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', ('Nouveau')) == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('gespro.annonce') 

        return super(Annonce, self).create(vals_list)

    def action_marquer_comme_lu(self):
        self.ensure_one() 
        self.state = 'lu'
        self.message_post(body=f"Annonce lue par {self.env.user.name}", message_type='notification', partner_ids=[(self.env.user.partner_id.id)])  

    def action_marquer_comme_non_lu(self):
        self.ensure_one() 
        self.state = 'non_lu'