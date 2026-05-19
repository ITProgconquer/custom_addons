from odoo import models, fields, api


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

    ceo_decision_comment = fields.Text(
        string="Commentaire décision CEO"
    )

    investigation_result = fields.Text(
        string="Résultat investigation (RESADMIN)"
    )

    # ─── RELATIONS ──────────────────────────────

    payment_ids = fields.One2many(
        'gespro.payment',
        'annonce_id',
        string="Paiements"
    )

    appel_ids = fields.One2many(
        'gespro.appel',
        'annonce_id',
        string="Appels à Concurrence"
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
            from odoo.exceptions import AccessError
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