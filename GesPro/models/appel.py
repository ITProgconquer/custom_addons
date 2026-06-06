from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError
from datetime import date


class Appel(models.Model):
    _name = "gespro.appel"
    _description = "Appel à Concurrence"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date_publication desc"

    # ─── RÉFÉRENCE ──────────────────────────────
    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default="Nouveau"
    )

    # ─── INFORMATIONS GÉNÉRALES ────────────────
    titre = fields.Char(string="Titre", required=True)

    type_appel = fields.Selection([
        ('unique', 'Lot unique'),
        ('allotti', 'Alloti'),
    ], string="Type d'appel", required=True, default='unique')

    lot_count = fields.Integer(string="Nombre de lots", default=1)

    procedure = fields.Selection([
        ('ao', "Appel d'offres"),
        ('cotation', 'Demande de cotation'),
        ('consultation', 'Consultation'),
        ('prix', 'Demande de prix'),
        ('autre', 'Autres'),
    ], string="Procédure", required=True)

    source = fields.Char(string="Source")

    date_publication = fields.Date(string="Date de publication", required=True)
    deadline = fields.Date(string="Date limite", required=True)

    delai_restant = fields.Integer(
        string="Délai restant (jours)",
        compute='_compute_delai_restant',
        store=True,
        index=True
    )

    last_alert_sent = fields.Date(string="Dernière alerte envoyée")

    # ─── NOUVEAUX CHAMPS ────────────────────────
    garantie_soumission = fields.Float(string="Garantie de soumission")
    autorite_contractante = fields.Char(string="Autorité contractante")

    # ─── RELATIONS ──────────────────────────────
    offre_id = fields.Many2one(
        'gespro.appel.offre',
        string="Appel d'offre source",
        required=True,
        ondelete='restrict'
    )

    # Le lien vers l'annonce est automatiquement hérité de l'appel d'offre
    annonce_id = fields.Many2one(
        'gespro.annonce',
        string="Annonce source",
        related='offre_id.annonce_id',
        store=True,
        readonly=True,
        ondelete='restrict'
    )

    pm_id = fields.Many2one(
        'res.users',
        string="PM Responsable",
        default=lambda self: self.env.user,
        required=True
    )

    depouillement_ids = fields.One2many(
        'gespro.depouillement', 
        'appel_id', 
        string="Dépouillements"
    )

    lot_ids = fields.One2many('gespro.lot', 'appel_id', string="Lots")
    checklist_ids = fields.One2many('gespro.checklist.line', 'appel_id', string="Checklists")

    # ─── CHECKLISTS PAR CATÉGORIE (Many2many calculés) ────
    checklist_tech_ids = fields.Many2many(
        'gespro.checklist.line', string="Checklist Technique",
        compute='_compute_checklist_categories', inverse='_inverse_checklist_categories',
        relation='gespro_appel_checklist_tech_rel', column1='appel_id', column2='line_id',
        domain=[('categorie', '=', 'tech')]
    )
    checklist_admin_ids = fields.Many2many(
        'gespro.checklist.line', string="Checklist Admin",
        compute='_compute_checklist_categories', inverse='_inverse_checklist_categories',
        relation='gespro_appel_checklist_admin_rel', column1='appel_id', column2='line_id',
        domain=[('categorie', '=', 'admin')]
    )
    checklist_fin_ids = fields.Many2many(
        'gespro.checklist.line', string="Checklist Financier",
        compute='_compute_checklist_categories', inverse='_inverse_checklist_categories',
        relation='gespro_appel_checklist_fin_rel', column1='appel_id', column2='line_id',
        domain=[('categorie', '=', 'fin')]
    )

    # ─── PROGRESSION ────────────────────────────
    progression_tech = fields.Float(compute='_compute_progression', store=True)
    progression_admin = fields.Float(compute='_compute_progression', store=True)
    progression_fin = fields.Float(compute='_compute_progression', store=True)
    progression_generale = fields.Float(compute='_compute_progression', store=True)

    # ─── WORKFLOW ───────────────────────────────
    state = fields.Selection([
        ('en_preparation', 'En préparation'),
        ('pret', 'Prêt à soumettre'),
        ('soumis', 'Soumis'),
        ('gagne', 'Gagné'),
        ('perdu', 'Perdu'),
        ('annule', 'Annulé'),
    ], string="Statut", default='en_preparation', tracking=True)

    active = fields.Boolean(string="Actif", default=True)
    color_kanban = fields.Integer(compute='_compute_color', store=True)
    show_generate_lots = fields.Boolean(compute='_compute_show_buttons')
    show_generate_checklists = fields.Boolean(compute='_compute_show_buttons')

    # ─── FILTRE DYNAMIQUE ───────────────────────
    active_checklist_filter = fields.Selection([
        ('all', 'Toutes'), ('tech', 'Technique'), ('admin', 'Administratif'), ('fin', 'Financier'),
    ], string="Filtre checklists", default='all')

    # ─── MÉTHODES ───────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('gespro.appel')
        records = super().create(vals_list)
        for record in records:
            template = self.env.ref('GesPro.mail_template_appel_creation', raise_if_not_found=False)
            if template:
                gespro_users = self.env['res.users'].search([
                    ('groups_id', 'in', [
                        self.env.ref('GesPro.group_ceo').id,
                        self.env.ref('GesPro.group_pm').id,
                        self.env.ref('GesPro.group_resadmin').id,
                        self.env.ref('GesPro.group_tech').id,
                        self.env.ref('GesPro.group_fin').id,
                    ])
                ])
                emails = ','.join(gespro_users.mapped('email'))
                if emails:
                    template.send_mail(
                        record.id,
                        force_send=True,
                        email_values={'email_to': emails}
                    )

    def action_go(self):
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            raise AccessError("Seul le CEO peut donner le GO.")
        self.state = 'en_preparation'
        self.message_post(body=f"🟢 GO donné par {self.env.user.name}")

    def action_no_go(self):
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            raise AccessError("Seul le CEO peut donner le NO GO.")
        self.state = 'annule'
        self.message_post(body=f"🔴 NO GO donné par {self.env.user.name}")

    @api.depends('deadline')
    def _compute_delai_restant(self):
        for record in self:
            if record.deadline:
                record.delai_restant = (record.deadline - date.today()).days
            else:
                record.delai_restant = 0

    @api.depends('delai_restant')
    def _compute_color(self):
        for record in self:
            if record.delai_restant <= 2:
                record.color_kanban = 1
            elif record.delai_restant <= 5:
                record.color_kanban = 4
            else:
                record.color_kanban = 0

    @api.depends('checklist_tech_ids.is_done', 'checklist_admin_ids.is_done', 'checklist_fin_ids.is_done')
    def _compute_progression(self):
        for record in self:
            record.progression_tech = self._calc_pct(record.checklist_tech_ids)
            record.progression_admin = self._calc_pct(record.checklist_admin_ids)
            record.progression_fin = self._calc_pct(record.checklist_fin_ids)
            categories = [record.progression_tech, record.progression_admin, record.progression_fin]
            non_zero = [p for p in categories if p > 0] or [0]
            record.progression_generale = sum(non_zero) / len(non_zero)

    def _calc_pct(self, lines):
        total = len(lines)
        if total == 0:
            return 0
        done = len(lines.filtered('is_done'))
        return (done / total) * 100

    @api.depends('checklist_ids')
    def _compute_checklist_categories(self):
        for record in self:
            record.checklist_tech_ids = record.checklist_ids.filtered(lambda l: l.categorie == 'tech')
            record.checklist_admin_ids = record.checklist_ids.filtered(lambda l: l.categorie == 'admin')
            record.checklist_fin_ids = record.checklist_ids.filtered(lambda l: l.categorie == 'fin')

    def _inverse_checklist_categories(self):
        pass

    @api.constrains('deadline', 'date_publication')
    def _check_dates(self):
        for record in self:
            if record.deadline and record.date_publication and record.deadline < record.date_publication:
                raise UserError("La date limite ne peut pas être antérieure à la date de publication.")

    @api.onchange('type_appel')
    def _onchange_type_appel(self):
        if self.type_appel == 'unique':
            self.lot_count = 1

    # --- Actions métier ---
    def action_generate_lots(self):
        self.ensure_one()
        self.lot_ids.unlink()
        if self.type_appel == 'unique':
            self.env['gespro.lot'].create({
                'appel_id': self.id, 'lot_num': 1, 'titre': self.titre or 'Lot unique',
            })
        else:
            for i in range(1, self.lot_count + 1):
                self.env['gespro.lot'].create({
                    'appel_id': self.id, 'lot_num': i, 'titre': f'Lot {i}',
                })
        self.message_post(body="✅ Lots générés avec succès.")

    def action_add_checklist_item(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ajouter une tâche',
            'res_model': 'gespro.checklist.line',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_appel_id': self.id,
                'default_categorie': self.env.context.get('default_categorie', 'tech'),
            },
        }

    # --- Décision CEO sur l'Appel ---
    def action_go(self):
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            raise AccessError("Seul le CEO peut donner le GO.")
        self.state = 'go'
        self.message_post(body=f"🟢 GO donné par {self.env.user.name}")

    def action_no_go(self):
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            raise AccessError("Seul le CEO peut donner le NO GO.")
        self.state = 'no_go'
        self.message_post(body=f"🔴 NO GO donné par {self.env.user.name}")

    # --- Validation et soumission ---
   
    def action_valider(self):
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            raise AccessError("Seul le CEO peut valider.")
        all_checklists = self.checklist_tech_ids | self.checklist_admin_ids | self.checklist_fin_ids
        incomplete = all_checklists.filtered(lambda l: not l.is_done)
        if incomplete:
            raise UserError(f"Checklist incomplète : {len(incomplete)} tâche(s) non cochée(s).")
        self.state = 'pret'
        self.message_post(body=f"✅ Dossier validé par {self.env.user.name} — Prêt à soumettre")
        # Email tout le monde
        template = self.env.ref('GesPro.mail_template_appel_valider', raise_if_not_found=False)
        if template:
            emails = self.env['gespro.annonce']._get_all_gespro_emails()
            if emails:
                template.send_mail(self.id, force_send=True, email_values={'email_to': emails})

    def action_soumettre(self):
        self.ensure_one()
        all_checklists = self.checklist_tech_ids | self.checklist_admin_ids | self.checklist_fin_ids
        if not all(all_checklists.mapped('is_done')):
            raise UserError("Checklist incomplète. Toutes les tâches doivent être cochées.")
        self.state = 'soumis'
        partners = self.pm_id.partner_id | self.annonce_id.user_id.partner_id | self.env.user.partner_id
        self.notify_users(
            partner_ids=partners.ids,
            body=f"📦 L'appel à concurrence {self.name} a été soumis."
        )
        # Email tout le monde
        template = self.env.ref('GesPro.mail_template_appel_soumission', raise_if_not_found=False)
        if template:
            emails = self.env['gespro.annonce']._get_all_gespro_emails()
            if emails:
                template.send_mail(self.id, force_send=True, email_values={'email_to': emails})

    def notify_users(self, partner_ids, body):
        """Poste un message dans le chatter et envoie une notification aux partenaires."""
        self.ensure_one()
        self.message_post(
            body=body,
            message_type='notification',
            partner_ids=partner_ids,
        )

    def action_gagne(self):
        self.ensure_one()
        self.state = 'gagne'
        self.message_post(body="🎉 Félicitations ! Dossier gagné !", message_type='notification')
        template = self.env.ref('GesPro.mail_template_appel_gagne', raise_if_not_found=False)
        if template:
            emails = self.env['gespro.annonce']._get_all_gespro_emails()
            if emails:
                template.send_mail(self.id, force_send=True, email_values={'email_to': emails})

    def action_perdu(self):
        self.ensure_one()
        self.state = 'perdu'
        self.message_post(body="Dossier non retenu", message_type='notification')
        template = self.env.ref('GesPro.mail_template_appel_perdu', raise_if_not_found=False)
        if template:
            emails = self.env['gespro.annonce']._get_all_gespro_emails()
            if emails:
                template.send_mail(self.id, force_send=True, email_values={'email_to': emails})

    def action_annuler(self):
        self.ensure_one()
        self.state = 'annule'

    def action_reouvrir(self):
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            raise AccessError("Seul le CEO peut rouvrir un dossier.")
        self.state = 'en_preparation'

    def set_checklist_filter(self):
        self.ensure_one()
        self.active_checklist_filter = self.env.context.get('filter', 'all')

    # --- Cron d'alertes ---
    def _cron_check_deadlines(self):
        today = date.today()
        appels = self.search([
            ('state', 'in', ['en_preparation', 'pret']),
            ('deadline', '>=', today),
        ])
        for appel in appels:
            days_left = (appel.deadline - today).days
            if days_left in (5, 2, 1, 0) and appel.last_alert_sent != today:
                template_xmlid = 'GesPro.mail_template_alert_j5' if days_left > 2 else 'GesPro.mail_template_alert_j2'
                template = self.env.ref(template_xmlid, raise_if_not_found=False)
                if template:
                    # Récupérer tous les utilisateurs des groupes GESPRO
                    gespro_users = self.env['res.users'].search([
                        ('groups_id', 'in', [
                            self.env.ref('GesPro.group_ceo').id,
                            self.env.ref('GesPro.group_pm').id,
                            self.env.ref('GesPro.group_resadmin').id,
                            self.env.ref('GesPro.group_tech').id,
                            self.env.ref('GesPro.group_fin').id,
                        ])
                    ])
                    emails = ','.join(gespro_users.mapped('email'))
                    if emails:
                        template.send_mail(
                            appel.id,
                            force_send=True,
                            email_values={'email_to': emails}
                        )
                # Notification chatter en plus
                appel.message_post(
                    body=f"⚠️ Alerte : {days_left} jours restants pour {appel.name}",
                    message_type='notification'
                )
                appel.write({'last_alert_sent': today})

    def write(self, vals):
        user = self.env.user
        if user.has_group('GesPro.group_tech') or user.has_group('GesPro.group_fin'):
            allowed_fields = ['checklist_tech_ids', 'checklist_admin_ids', 'checklist_fin_ids']
            for field in vals:
                if field not in allowed_fields:
                    raise AccessError("Vous ne pouvez modifier que les checklists.")
        if user.has_group('GesPro.group_resadmin'):
            allowed_fields = ['state', 'checklist_tech_ids', 'checklist_admin_ids', 'checklist_fin_ids']
            for field in vals:
                if field not in allowed_fields:
                    raise AccessError("Vous ne pouvez modifier que le statut et les checklists.")
        return super().write(vals)

    @api.depends('lot_ids', 'checklist_ids')
    def _compute_show_buttons(self):
        for record in self:
            record.show_generate_lots = len(record.lot_ids) == 0
            record.show_generate_checklists = len(record.checklist_ids) == 0