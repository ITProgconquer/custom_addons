from odoo import models, fields


class Payment(models.Model):
    _name = "gespro.payment"
    _description = "Paiement des frais d'accès au dossier"
    _order = "payment_date desc"

    offre_id = fields.Many2one(
        'gespro.appel.offre',
        string="Appel d'offre",
        required=True,
        ondelete='cascade'
    )

    amount = fields.Float(
        string="Montant payé",
        required=True,
        digits=(16, 2)
    )

    currency_id = fields.Many2one(
        'res.currency',
        string="Devise",
        default=lambda self: self.env.ref('base.XOF')
    )

    payment_date = fields.Date(
        string="Date de paiement",
        required=True,
        default=fields.Date.today
    )

    proof = fields.Binary(string="Preuve de paiement")

    proof_filename = fields.Char(string="Nom du fichier preuve")

    state = fields.Selection([
        ('pending', 'En attente'),
        ('paid', 'Payé'),
        ('rejected', 'Rejeté'),
    ], string="Statut", default='pending')

    document_files = fields.Many2many(
        'ir.attachment',
        'gespro_payment_ir_attachments_rel',
        'payment_id',
        'attachment_id',
        string="Dossier complet acquis",
        domain="[('res_model', '=', 'gespro.payment')]"
    )

    note = fields.Text(string="Commentaire")



    def action_confirm_paid(self):
        self.ensure_one()
        self.state = 'paid'
        if self.offre_id:
            self.offre_id.message_post(body=f"Le paiement de {self.amount} a été confirmé pour l'offre {self.offre_id.name}.")
            # Destinataires : tous les CEO (groupe) + le PM de l'offre
            # On exclut l'expéditeur (RESADMIN) et l'admin système
            ceo_users = self.env['res.users'].search([
                ('groups_id', 'in', [self.env.ref('GesPro.group_ceo').id]),
                ('id', '!=', self.env.user.id),
                ('login', '!=', 'admin'),
            ])
            pm = self.offre_id.pm_id
            recipients = []
            # Ajouter les CEO
            for ceo in ceo_users:
                if ceo.email:
                    recipients.append(ceo.email)
            # Ajouter le PM, sauf si c'est l'expéditeur ou admin
            if pm and pm.id != self.env.user.id and pm.login != 'admin' and pm.email:
                recipients.append(pm.email)
            # Envoyer l'email
            if recipients:
                template = self.env.ref('GesPro.mail_template_payment_confirmed', raise_if_not_found=False)
                if template:
                    template.send_mail(
                        self.offre_id.id,
                        force_send=True,
                        email_values={'email_to': ','.join(recipients)}
                    )
    
        # Email CEO + PM
        template = self.env.ref('GesPro.mail_template_payment_confirmed', raise_if_not_found=False)
        if template and self.offre_id:
            ceo = self.offre_id.annonce_id.user_id
            pm = self.offre_id.pm_id
            recipients = ','.join([ceo.email, pm.email] if ceo.email and pm.email else [])
            if recipients:
                # Note : le template attend un objet de type appel d'offre, on passe l'offre_id
                template.send_mail(
                    self.offre_id.id,
                    force_send=True,
                    email_values={'email_to': recipients}
                )


    def action_reject(self):
        self.ensure_one()
        self.state = 'rejected'

    def action_reset_pending(self):
        self.ensure_one()
        self.state = 'pending'