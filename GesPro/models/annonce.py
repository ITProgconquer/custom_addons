from odoo import models, fields, api
from odoo.exceptions import AccessError


class Annonce(models.Model):
    _name = "gespro.annonce"
    _description = "Annonce (conteneur d'appels d'offre)"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date_envoi desc"

    # ─── RÉFÉRENCE ──────────────────────────────
    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default="Nouveau"
    )

    # ─── DOCUMENTS ──────────────────────────────
    source_file = fields.Binary(string="Fichier source (PDF/DOCX)")
    source_filename = fields.Char(string="Nom du fichier source")

    # ─── INFORMATIONS ───────────────────────────
    description = fields.Text(string="Description")

    date_envoi = fields.Datetime(
        string="Date d'envoi",
        default=fields.Datetime.now,
        readonly=True
    )

    user_id = fields.Many2one(
        'res.users',
        string="Auteur",
        default=lambda self: self.env.user,
        readonly=True
    )

    # ─── RELATIONS ──────────────────────────────
    # Remplacé par la liste des appels d'offre
    appel_offre_ids = fields.One2many('gespro.appel.offre', 'annonce_id', string="Appels d'offre")

    # ─── CHAMPS D'AFFICHAGE AVEC ÉMOJIS ─────────
    display_reference = fields.Char(
        string="Référence",
        compute='_compute_display_reference',
        store=False
    )
    display_author = fields.Char(
        string="Auteur",
        compute='_compute_display_author',
        store=False
    )
    display_date = fields.Char(
        string="Date d'envoi",
        compute='_compute_display_date',
        store=False
    )
    active = fields.Boolean(string="Actif", default=True)

    # ─── MÉTHODES ───────────────────────────────
    def _get_all_gespro_emails(self):
        """Retourne une chaîne d'emails de tous les utilisateurs appartenant aux groupes GESPRO."""
        groups = [
            self.env.ref('GesPro.group_ceo').id,
            self.env.ref('GesPro.group_pm').id,
            self.env.ref('GesPro.group_resadmin').id,
            self.env.ref('GesPro.group_tech').id,
            self.env.ref('GesPro.group_fin').id,
        ]
        users = self.env['res.users'].search([('groups_id', 'in', groups)])
        return ','.join(users.mapped('email'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        template = self.env.ref('GesPro.mail_template_annonce_creation', raise_if_not_found=False)
        if template:
            emails = self.env['gespro.annonce']._get_all_gespro_emails()
            if emails:
                for record in records:
                    template.send_mail(record.id, force_send=True, email_values={'email_to': emails})
        return records
    
    def action_create_appel_offre(self):
        """Ouvre le formulaire de création d'un Appel d'offre lié à cette annonce"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Créer un Appel d\'offre',
            'res_model': 'gespro.appel.offre',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_annonce_id': self.id,
            },
        }

    def open_appel_offre_list(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f"Appels d'offre de {self.name}",
            'res_model': 'gespro.appel.offre',
            'view_mode': 'list,kanban,form',
            'domain': [('annonce_id', '=', self.id)],
            'target': 'current',
        }

    # ─── COMPUTE POUR LES CHAMPS D'AFFICHAGE ────
    @api.depends('name')
    def _compute_display_reference(self):
        for record in self:
            record.display_reference = f"📄 {record.name}" if record.name else ""

    @api.depends('user_id')
    def _compute_display_author(self):
        for record in self:
            record.display_author = f"👤 {record.user_id.name}" if record.user_id else ""

    @api.depends('date_envoi')
    def _compute_display_date(self):
        for record in self:
            record.display_date = f"📅 {record.date_envoi.strftime('%Y-%m-%d')}" if record.date_envoi else ""
