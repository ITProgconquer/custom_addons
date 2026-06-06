from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError




class AppelOffre(models.Model):
    _name = "gespro.appel.offre"
    _description = "Appel d'offre"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date_butoire desc"

    # ─── RÉFÉRENCE ──────────────────────────────
    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default="Nouveau"
    )

    # ─── INFORMATIONS ───────────────────────────
    titre = fields.Char(string="Nom de l'offre", required=True)
    date_butoire = fields.Date(string="Date butoire", required=True)
    garantie_soumission = fields.Float(string="Garantie de soumission")
    autorite_contractante = fields.Char(string="Autorité contractante")


    capture_ids = fields.Many2many(
        'ir.attachment',
        'gespro_offre_ir_attachments_rel',
        'offre_id',
        'attachment_id',
        string="Captures d'écran",
        help="Ajoutez des captures d'écran ou d'autres documents"
    )

    # ─── RELATIONS ──────────────────────────────
    annonce_id = fields.Many2one(
        'gespro.annonce',
        string="Annonce source",
        required=True,
        ondelete='restrict'
    )
    pm_id = fields.Many2one(
        'res.users',
        string="PM Responsable",
        default=lambda self: self.env.user,
        required=True
    )
    appel_concurrence_ids = fields.One2many(
        'gespro.appel',
        'offre_id',
        string="Appels à Concurrence"
    )

    payment_ids = fields.One2many(
        'gespro.payment',
        'offre_id',
        string="Paiements"
    )

    

    can_create_appel = fields.Boolean(
        string="Peut créer un AC",
        compute='_compute_can_create_appel'
    )

    investigation_result = fields.Text(string="Résultat investigation (RESADMIN)")

    # ─── WORKFLOW (anciens états réintégrés) ────
    state = fields.Selection([
        ('nouveau', 'Nouveau'),
        ('lu', 'Lu'),
        ('en_investigation', 'En investigation'),
        ('go', 'GO'),
        ('no_go', 'NO GO'),
        ('ignore', 'Ignoré'),
    ], string="Statut", default='nouveau', tracking=True)

    active = fields.Boolean(string="Actif", default=True)

    # ─── MÉTHODES ───────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('gespro.appel.offre')
        records = super().create(vals_list)
        template = self.env.ref('GesPro.mail_template_offre_creation', raise_if_not_found=False)
        if template:
            emails = self.env['gespro.annonce']._get_all_gespro_emails()
            if emails:
                for record in records:
                    template.send_mail(record.id, force_send=True, email_values={'email_to': emails})
        return records

    def notify_users(self, partner_ids, body):
        """Poste un message dans le chatter et envoie une notification aux partenaires."""
        self.ensure_one()
        self.message_post(
            body=body,
            message_type='notification',
            partner_ids=partner_ids,
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('gespro.appel.offre')
        return super().create(vals_list)

    # --- Actions CEO ---
    def action_mark_lu(self):
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            raise AccessError("Seul le CEO peut marquer comme lu.")
        self.state = 'lu'
        self.message_post(body=f"📖 Appel d'offre lu par {self.env.user.name}")

    def action_investigation(self):
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            raise AccessError("Seul le CEO peut demander une investigation.")
        self.state = 'en_investigation'
        # Notification interne
        partners = self.pm_id.partner_id | self.annonce_id.user_id.partner_id | self.env.user.partner_id
        self.notify_users(
            partner_ids=partners.ids,
            body=f"🔍 Investigation demandée par {self.env.user.name} pour l'appel d'offre {self.name}."
        )
        # Email au RESADMIN
        resadmin_users = self.env['res.users'].search([('groups_id', 'in', [self.env.ref('GesPro.group_resadmin').id])])
        if resadmin_users:
            template = self.env.ref('GesPro.mail_template_investigation', raise_if_not_found=False)
            if template:
                template.send_mail(
                    self.id,
                    force_send=True,
                    email_values={'email_to': ','.join(resadmin_users.mapped('email'))}
                )

    def action_go(self):
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            raise AccessError("Seul le CEO peut donner le GO.")
        self.state = 'go'
        # Notification interne
        partners = self.pm_id.partner_id | self.annonce_id.user_id.partner_id | self.env.user.partner_id
        self.notify_users(
            partner_ids=partners.ids,
            body=f"🟢 GO donné par {self.env.user.name} pour l'appel d'offre {self.name}."
        )
        # Email tout le monde
        template = self.env.ref('GesPro.mail_template_offre_go', raise_if_not_found=False)
        if template:
            emails = self.env['gespro.annonce']._get_all_gespro_emails()
            if emails:
                template.send_mail(self.id, force_send=True, email_values={'email_to': emails})

    def action_no_go(self):
        """CEO refuse l'appel d'offre en ouvrant le wizard de motif"""
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            raise AccessError("Seul le CEO peut donner le NO GO.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Motif du NO GO',
            'res_model': 'gespro.appel.offre.ignore.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_offre_id': self.id,
            },
        }
    
    def action_ignore(self):
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            raise AccessError("Seul le CEO peut ignorer l'appel d'offre.")
        self.state = 'ignore'

    @api.depends('state', 'payment_ids.state')
    def _compute_can_create_appel(self):
        for record in self:
            record.can_create_appel = (
                record.state == 'go' and 
                record.payment_ids and 
                any(p.state == 'paid' for p in record.payment_ids)
            )

    def action_create_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enregistrer un paiement',
            'res_model': 'gespro.payment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_offre_id': self.id,
            },
        }

    # --- Création d'un Appel à Concurrence (PM) ---
    def action_create_appel_concurrence(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Créer un Appel à Concurrence',
            'res_model': 'gespro.appel',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_offre_id': self.id,
                'default_annonce_id': self.annonce_id.id,
            },
        }
    
    def open_appel_concurrence(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appel à Concurrence',
            'res_model': 'gespro.appel',
            'view_mode': 'form',
            'res_id': self.appel_concurrence_ids[0].id,
            'target': 'current',
        }
    

    def open_payment_list(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Paiements',
            'res_model': 'gespro.payment',
            'view_mode': 'list,form',
            'domain': [('offre_id', '=', self.id)],
            'target': 'current',
        }
