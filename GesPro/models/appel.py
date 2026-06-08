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
    checklist_ids = fields.One2many('gespro.checklist.line','appel_id',string="Toutes les checklists")


    # ─── CHECKLISTS PAR CATÉGORIE (Many2many calculés) ────
    checklist_tech_ids = fields.One2many('gespro.checklist.line', 'appel_id', 
        domain=[('categorie', '=', 'tech')], string="Checklist Technique")
    checklist_admin_ids = fields.One2many('gespro.checklist.line', 'appel_id', 
        domain=[('categorie', '=', 'admin')], string="Checklist Admin")
    checklist_fin_ids = fields.One2many('gespro.checklist.line', 'appel_id', 
        domain=[('categorie', '=', 'fin')], string="Checklist Financier")

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
            # Template de notification de création (inchangé)
            template = self.env.ref('GesPro.mail_template_appel_creation', raise_if_not_found=False)
            if template:
                # Le CC sera automatiquement le CEO auteur de l'annonce, via annonce_id.user_id.email
                template.send_mail(record.id, force_send=True)
        return records

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

    @api.depends('checklist_tech_ids.state', 'checklist_admin_ids.state', 'checklist_fin_ids.state')
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
        done = len(lines.filtered(lambda l: l.state == 'done'))
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
            from odoo.exceptions import AccessError
            raise AccessError("Seul le CEO peut valider.")
        all_checklists = self.checklist_tech_ids | self.checklist_admin_ids | self.checklist_fin_ids
        if not all(all_checklists.mapped(lambda l: l.state == 'done')):
            from odoo.exceptions import UserError
            raise UserError("Checklist incomplète. Toutes les tâches doivent être terminées.")
        self.state = 'pret'
        self.message_post(body=f"✅ Dossier validé par {self.env.user.name} — Prêt à soumettre")

    def action_soumettre(self):
        self.ensure_one()
        all_checklists = self.checklist_tech_ids | self.checklist_admin_ids | self.checklist_fin_ids
        if not all(all_checklists.mapped(lambda l: l.state == 'done')):
            from odoo.exceptions import UserError
            raise UserError("Checklist incomplète. Toutes les tâches doivent être terminées.")
        self.state = 'soumis'
        self.message_post(body="📦 Dossier soumis")


    def action_gagne(self):
        self.ensure_one()
        self.state = 'gagne'
        self.message_post(body="🎉 Félicitations ! Dossier gagné !", message_type='notification')

    def action_perdu(self):
        self.ensure_one()
        self.state = 'perdu'
        self.message_post(body="Dossier non retenu", message_type='notification')

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
                template_xmlid = 'gespro.mail_template_alert_j5' if days_left > 2 else 'gespro.mail_template_alert_j2'
                template = self.env.ref(template_xmlid, raise_if_not_found=False)
                if template:
                    template.send_mail(appel.id, force_send=True)
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