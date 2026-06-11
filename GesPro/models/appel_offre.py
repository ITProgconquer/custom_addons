from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError
import logging

_logger = logging.getLogger(__name__)



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
    titre = fields.Char(string="Objet", required=True)
    date_butoire = fields.Date(string="Date limite de dépôt", required=True)
    garantie_soumission = fields.Float(string="Montant de la garantie de soumission")
    autorite_contractante = fields.Char(string="Nom de l'autorité contractante")
    lot_count = fields.Integer(string="Nombre de lots", default=1)
    ligne_de_credit = fields.Integer(string="Ligne de crédit associée")
    chiffre_affaire = fields.Char(string="Chiffre d'affaire sur tant d'année(s)")
    visite_site = fields.Date(string="Visite de site requise",required=False)
    ceo_comment = fields.Text(string="Commentaire du CEO", readonly=True)
    frais_des_doosiers = fields.Integer(string="Frais des dossiers", default=0)
    type_appel = fields.Selection([
        ('unique', 'Lot unique'),
        ('allotti', 'Alloti'),
    ], string="Type", default='unique')


    lot_ids = fields.One2many('gespro.lot', 'offre_id', string="Lots")

    show_generate_lots = fields.Boolean(compute='_compute_show_generate_lots')

    

    capture = fields.Binary(string="Capture d'écran")
    capture_filename = fields.Char(string="Ajoutez des captures d'écran ou d'autres documents")

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



    show_create_ac = fields.Boolean(compute='_compute_show_create_ac')

    can_create_appel = fields.Boolean(
        string="Peut créer un AC",
        compute='_compute_can_create_appel'
    )

    investigation_result_ids = fields.Many2many(
        'ir.attachment',
        'gespro_offre_investigation_attachments_rel',
        'offre_id',
        'attachment_id',
        string="Résultats d'investigation"
    )

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

    type_offre = fields.Selection([
        ('DC', 'DC'),
        ('DPX', 'DPX'),
        ('AO', 'AO'),
        ('CC', 'CC'),
        ('MANIF', 'Manif'),
    ], string="Type d'offre", required=True)

    name = fields.Char(string="Référence", readonly=True, copy=False)

    @api.depends('state', 'payment_ids.state')
    def _compute_show_create_ac(self):
        for record in self:
            record.show_create_ac = (
                record.state == 'go' and 
                record.payment_ids and 
                any(p.state == 'paid' for p in record.payment_ids) and
                not record.appel_concurrence_ids
            )

    # ─── MÉTHODES ───────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            type_offre = vals.get('type_offre', 'AO')
            seq_code = f'gespro.appel.offre.{type_offre}'
            vals['name'] = self.env['ir.sequence'].next_by_code(seq_code)
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('gespro.appel.offre')
        records = super().create(vals_list)
        template = self.env.ref('GesPro.mail_template_offre_creation', raise_if_not_found=False)
        if template:
            emails = self.env['gespro.annonce']._get_all_gespro_emails(exclude_user=self.env.user)
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
        return {
            'type': 'ir.actions.act_window',
            'name': 'Demander une investigation',
            'res_model': 'gespro.appel.offre.investigation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_offre_id': self.id,
            },
        }


    def action_send_investigation_result(self):
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_resadmin'):
            raise AccessError("Seul le RESADMIN peut transmettre le résultat.")
        # Rechercher les utilisateurs ayant le groupe CEO
        ceo_users = self.env['res.users'].search([
            ('groups_id', 'in', [self.env.ref('GesPro.group_ceo').id]),
            ('id', '!=', self.env.user.id),
            ('login', '!=', 'admin'),
        ])
        recipients = ','.join(ceo_users.mapped('email'))
        if recipients:
            template = self.env.ref('GesPro.mail_template_investigation_result', raise_if_not_found=False)
            if template:
                template.send_mail(
                    self.id,
                    force_send=True,
                    email_values={'email_to': recipients}
                )
        self.message_post(body=f"📨 Résultat d'investigation transmis au CEO par {self.env.user.name}.")                

    def action_go(self):
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            raise AccessError("Seul le CEO peut donner le GO.")
        self.state = 'go'
        # Notification interne
        # partners = self.pm_id.partner_id | self.annonce_id.user_id.partner_id | self.env.user.partner_id
        # self.notify_users(
        #     partner_ids=partners.ids,
        #     body=f"🟢 GO donné par {self.env.user.name} pour l'appel d'offre {self.name}."
        # )
        # Email tout le monde
        template = self.env.ref('GesPro.mail_template_offre_go', raise_if_not_found=False)
        if template:
            emails = self.env['gespro.annonce']._get_all_gespro_emails(exclude_user=self.env.user)
            if emails:
                template.send_mail(self.id, force_send=True, email_values={'email_to': emails})

    def action_no_go(self):
        """CEO refuse l'appel d'offre en ouvrant le wizard de motif"""
        self.ensure_one()
        if not self.env.user.has_group('GesPro.group_ceo'):
            raise AccessError("Seul le CEO peut donner le NO GO.")
        
        # template = self.env.ref('GesPro.mail_template_offre_nogo', raise_if_not_found=False)
        # if template:
        #     emails = self.env['gespro.annonce']._get_all_gespro_emails(exclude_user=self.env.user)
        #     if emails:
        #         template.send_mail(self.id, force_send=True, email_values={'email_to': emails})


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
        
        ac = self.env['gespro.appel'].create({
            'offre_id': self.id,
            'annonce_id': self.annonce_id.id,
            'titre': self.titre,
            'autorite_contractante': self.autorite_contractante,
            'garantie_soumission': self.garantie_soumission,
            'pm_id': self.pm_id.id,
            'deadline': self.date_butoire,
            'date_publication': fields.Date.today(),
            'type_appel': self.type_appel,
            'lot_count': self.lot_count,
        })
        
        # Copier uniquement les lots
        for offre_lot in self.lot_ids:
            self.env['gespro.lot'].create({
                'appel_id': ac.id,
                'lot_num': offre_lot.lot_num,
                'titre': offre_lot.titre,
            })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appel à Concurrence',
            'res_model': 'gespro.appel',
            'view_mode': 'form',
            'res_id': ac.id,
            'target': 'current',
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
    
    def _sync_attachments(self):
        for record in self:
            if record.capture_ids:
                record.capture_ids.write({
                    'res_model': 'gespro.appel.offre',
                    'res_id': record.id,
                })
            
            if record.investigation_result_ids:
                record.investigation_result_ids.write({
                    'res_model': 'gespro.appel.offre',
                    'res_id': record.id,
                })

    
    def write(self, vals):
        res = super().write(vals)
        self._sync_attachments()
        return res
    

    @api.depends('lot_ids')
    def _compute_show_generate_lots(self):
        for record in self:
            record.show_generate_lots = not record.lot_ids


    def action_generate_lots(self):
        self.ensure_one()
        self.lot_ids.unlink()
        if self.type_appel == 'unique':
            self.env['gespro.lot'].create({
                'offre_id': self.id,
                'lot_num': 1,
                'titre': self.titre or 'Lot unique',
            })
        else:
            for i in range(1, self.lot_count + 1):
                self.env['gespro.lot'].create({
                    'offre_id': self.id,
                    'lot_num': i,
                    'titre': f'Lot {i}',
                })
        self.message_post(body="✅ Lots générés avec succès.")