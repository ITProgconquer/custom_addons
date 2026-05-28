from odoo import models, fields, api
from odoo.exceptions import AccessError


class Annonce(models.Model):
    _name = "gespro.annonce"
    _description = "Annonce de détection et investigation"
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

    # ─── WORKFLOW ───────────────────────────────

    state = fields.Selection([
        ('new', 'Nouveau'),
        ('lu', 'Lu'),
        ('en_investigation', 'En investigation'),
        ('go', 'GO'),
        ('no_go', 'NO GO'),
        ('ignore', 'Ignoré'),
    ], string="Statut", default='new', tracking=True)

    # ─── DÉCISION CEO ───────────────────────────

    ceo_capture_ids = fields.Many2many(
        'ir.attachment',
        string="Captures d'écran CEO"
    )
    ceo_decision_comment = fields.Text(string="Commentaire décision CEO")
    investigation_result = fields.Text(string="Résultat investigation (RESADMIN)")

    # ─── RELATIONS ──────────────────────────────

    payment_ids = fields.One2many('gespro.payment', 'annonce_id', string="Paiements")
    appel_ids = fields.One2many('gespro.appel', 'annonce_id', string="Appels à Concurrence")

    can_create_appel = fields.Boolean(
        string="Peut créer un AC",
        compute='_compute_can_create_appel'
    )

    # ─── CHAMPS D'AFFICHAGE AVEC ÉMOJIS (pour la vue liste) ─────────
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
    display_state = fields.Char(
        string="Statut",
        compute='_compute_display_state',
        store=False
    )
    display_date = fields.Char(
        string="Date d'envoi",
        compute='_compute_display_date',
        store=False
    )

    # ─── MÉTHODES ───────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('gespro.annonce')
        return super().create(vals_list)

    def action_mark_lu(self):
        """CEO marque l'annonce comme lue"""
        self.ensure_one()
        self.state = 'lu'
        self.message_post(
            body=f"📖 Annonce lue par {self.env.user.name}",
            message_type='notification',
            partner_ids=[self.user_id.partner_id.id]
        )

    def action_investigation(self):
        """CEO demande une investigation"""
        self.ensure_one()
        self.state = 'en_investigation'
        self.message_post(
            body=f"🔍 Investigation demandée par {self.env.user.name}",
            message_type='notification'
        )

    def action_go(self):
        """CEO valide le GO"""
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            raise AccessError("Seul le CEO peut donner le GO.")
        self.state = 'go'
        self.message_post(
            body=f"🟢 GO donné par {self.env.user.name}",
            message_type='notification'
        )

    def action_no_go(self):
        """CEO refuse (NO GO)"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Motif du NO GO',
            'res_model': 'gespro.annonce.ignore.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_annonce_id': self.id},
        }

    def action_ignore(self):
        """CEO ignore l'annonce"""
        self.ensure_one()
        self.state = 'ignore'

    @api.depends('state', 'payment_ids.state')
    def _compute_can_create_appel(self):
        for record in self:
            record.can_create_appel = (
                record.state == 'go' and 
                record.payment_ids and 
                any(p.state == 'paid' for p in record.payment_ids)
            )

    def action_create_appel(self):
        """Ouvre le formulaire de création d'Appel avec l'Annonce pré-remplie"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Créer un Appel à Concurrence',
            'res_model': 'gespro.appel',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_annonce_id': self.id,
                'default_titre': self.description or '',
            },
        }

    # ─── COMPUTE POUR LES CHAMPS D'AFFICHAGE (émoji + texte ensemble) ────
    @api.depends('name')
    def _compute_display_reference(self):
        for record in self:
            record.display_reference = f"📄 {record.name}" if record.name else ""

    @api.depends('user_id')
    def _compute_display_author(self):
        for record in self:
            record.display_author = f"👤 {record.user_id.name}" if record.user_id else ""

    @api.depends('state')
    def _compute_display_state(self):
        for record in self:
            state_label = dict(self._fields['state'].selection).get(record.state, record.state)
            record.display_state = f"🏷 {state_label}" if record.state else ""

    @api.depends('date_envoi')
    def _compute_display_date(self):
        for record in self:
            record.display_date = f"📅 {record.date_envoi.strftime('%Y-%m-%d')}" if record.date_envoi else ""