from odoo import api, models, fields


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

    def _sync_attachments(self):
        for record in self:
            if record.document_files:
                record.document_files.write({
                    'res_model': 'gespro.payment',
                    'res_id': record.id,
                })

    

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_attachments()
        return records
    
    def write(self, vals):
        res = super().write(vals)
        self._sync_attachments()
        return res

    def action_confirm_paid(self):
        self.ensure_one()
        self.state = 'paid'

    def action_reject(self):
        self.ensure_one()
        self.state = 'rejected'

    def action_reset_pending(self):
        self.ensure_one()
        self.state = 'pending'