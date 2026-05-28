from odoo import models, fields


class Payment(models.Model):
    _name = "gespro.payment"
    _description = "Paiement des frais d'accès au dossier"
    _order = "payment_date desc"

    annonce_id = fields.Many2one(
        'gespro.annonce',
        string="Annonce",
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

    def action_reject(self):
        self.ensure_one()
        self.state = 'rejected'

    def action_reset_pending(self):
        self.ensure_one()
        self.state = 'pending'
