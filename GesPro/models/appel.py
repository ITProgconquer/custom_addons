from odoo import models, fields, api
from odoo.exceptions import UserError
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

    lot_ids = fields.One2many(
        'gespro.lot',
        'appel_id',
        string="Lots"
    )

    checklist_ids = fields.One2many(
        'gespro.checklist.line',
        'appel_id',
        string="Checklists"
    )

    # ─── PROGRESSION ────────────────────────────

    progression_tech = fields.Float(
        string="Progression Technique (%)",
        compute='_compute_progression',
        store=True
    )
    progression_admin = fields.Float(
        string="Progression Admin (%)",
        compute='_compute_progression',
        store=True
    )
    progression_fin = fields.Float(
        string="Progression Financière (%)",
        compute='_compute_progression',
        store=True
    )
    progression_generale = fields.Float(
        string="Progression Générale (%)",
        compute='_compute_progression',
        store=True
    )

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

    color_kanban = fields.Integer(
        string="Couleur Kanban",
        compute='_compute_color',
        store=True
    )
    show_generate_lots = fields.Boolean(compute='_compute_show_buttons')
    show_generate_checklists = fields.Boolean(compute='_compute_show_buttons')

    checklist_tech_ids = fields.One2many('gespro.checklist.line', 'appel_id', 
        domain=[('categorie', '=', 'tech')], string="Checklist Technique")
    checklist_admin_ids = fields.One2many('gespro.checklist.line', 'appel_id', 
        domain=[('categorie', '=', 'admin')], string="Checklist Admin")
    checklist_fin_ids = fields.One2many('gespro.checklist.line', 'appel_id', 
        domain=[('categorie', '=', 'fin')], string="Checklist Financier")

    # ─── MÉTHODES ───────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('gespro.appel')
        return super().create(vals_list)

    @api.depends('deadline')
    def _compute_delai_restant(self):
        for record in self:
            if record.deadline:
                delta = record.deadline - date.today()
                record.delai_restant = delta.days
            else:
                record.delai_restant = 0

    @api.depends('delai_restant')
    def _compute_color(self):
        for record in self:
            if record.delai_restant <= 2:
                record.color_kanban = 1   # Rouge
            elif record.delai_restant <= 5:
                record.color_kanban = 4   # Orange
            else:
                record.color_kanban = 0   # Vert

    @api.depends('checklist_tech_ids.is_done', 'checklist_admin_ids.is_done', 'checklist_fin_ids.is_done')
    def _compute_progression(self):
        for record in self:
            record.progression_tech = self._calc_pct(record.checklist_tech_ids)
            record.progression_admin = self._calc_pct(record.checklist_admin_ids)
            record.progression_fin = self._calc_pct(record.checklist_fin_ids)
            record.progression_generale = (
                record.progression_tech +
                record.progression_admin +
                record.progression_fin
            ) / 3


    def _calc_pct(self, lines):
        total = len(lines)
        if total == 0:
            return 0
        done = len(lines.filtered('is_done'))
        return (done / total) * 100

    @api.constrains('deadline', 'date_publication')
    def _check_dates(self):
        for record in self:
            if record.deadline and record.date_publication:
                if record.deadline < record.date_publication:
                    raise UserError(
                        "La date limite ne peut pas être antérieure "
                        "à la date de publication."
                    )

    @api.onchange('type_appel')
    def _onchange_type_appel(self):
        if self.type_appel == 'unique':
            self.lot_count = 1

    def action_generate_lots(self):
        """Génère les lots selon le type d'appel"""
        self.ensure_one()
        self.lot_ids.unlink()

        if self.type_appel == 'unique':
            self.env['gespro.lot'].create({
                'appel_id': self.id,
                'lot_num': 1,
                'titre': self.titre or 'Lot unique',
            })
        else:
            for i in range(1, self.lot_count + 1):
                self.env['gespro.lot'].create({
                    'appel_id': self.id,
                    'lot_num': i,
                    'titre': f'Lot {i}',
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

    def action_valider(self):
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            from odoo.exceptions import AccessError
            raise AccessError("Seul le CEO peut valider.")
        
        # Vérifier toutes les checklists
        all_checklists = self.checklist_tech_ids | self.checklist_admin_ids | self.checklist_fin_ids
        incomplete = all_checklists.filtered(lambda l: not l.is_done)
        if incomplete:
            from odoo.exceptions import UserError
            raise UserError(
                f"Checklist incomplète : {len(incomplete)} tâche(s) non cochée(s)."
            )
        
        self.state = 'pret'
        self.message_post(body=f"✅ Dossier validé par {self.env.user.name} — Prêt à soumettre")



    def action_soumettre(self):
        self.ensure_one()
        all_checklists = self.checklist_tech_ids | self.checklist_admin_ids | self.checklist_fin_ids
        if not all(all_checklists.mapped('is_done')):
            from odoo.exceptions import UserError
            raise UserError(
                "Checklist incomplète. Toutes les tâches doivent être cochées."
            )
        self.state = 'soumis'
        self.message_post(body="📦 Dossier soumis")

    def action_gagne(self):
        self.ensure_one()
        self.state = 'gagne'
        self.message_post(
            body="🎉 Félicitations ! Dossier gagné !",
            message_type='notification'
        )

    def action_perdu(self):
        self.ensure_one()
        self.state = 'perdu'
        self.message_post(
            body="Dossier non retenu",
            message_type='notification'
        )

    def action_annuler(self):
        self.ensure_one()
        self.state = 'annule'

    def _cron_check_deadlines(self):
        """Méthode appelée par le cron toutes les heures"""
        today = date.today()
        appels = self.search([
            ('state', 'in', ['en_preparation', 'pret']),
            ('deadline', '>=', today),
        ])
        for appel in appels:
            if appel.delai_restant in (5, 2, 1, 0):
                if appel.last_alert_sent != today:
                    template = self.env.ref(
                        'gespro.mail_template_alert_j5' if appel.delai_restant > 2
                        else 'gespro.mail_template_alert_j2'
                    )
                    template.send_mail(appel.id, force_send=True)
                    appel.last_alert_sent = today
    
    def write(self, vals):
        user = self.env.user
        # TECH et FIN : uniquement checklists
        if user.has_group('GesPro.group_tech') or user.has_group('GesPro.group_fin'):
            allowed_fields = ['checklist_ids']
            for field in vals:
                if field not in allowed_fields:
                    raise api.AccessError("Vous ne pouvez modifier que les checklists.")
        # RESADMIN : uniquement state
        if user.has_group('GesPro.group_resadmin'):
            allowed_fields = ['state', 'checklist_ids']
            for field in vals:
                if field not in allowed_fields:
                    raise fields.AccessError("Vous ne pouvez modifier que le statut et les checklists.")
        return super().write(vals)
    
    
    @api.depends('lot_ids', 'checklist_ids')
    def _compute_show_buttons(self):
        for record in self:
            record.show_generate_lots = len(record.lot_ids) == 0
            record.show_generate_checklists = len(record.checklist_ids) == 0