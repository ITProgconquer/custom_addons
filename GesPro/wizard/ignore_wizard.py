from odoo import models, fields


class AnnonceIgnoreWizard(models.TransientModel):
    _name = "gespro.annonce.ignore.wizard"
    _description = "Assistant de refus d'annonce (NO GO / Ignoré)"

    annonce_id = fields.Many2one(
        'gespro.annonce',
        string="Annonce",
        required=True
    )

    motif = fields.Text(
        string="Motif",
        required=True
    )

    def action_confirm(self):
        """Confirme le refus et met à jour l'annonce"""
        self.ensure_one()
        self.annonce_id.write({
            'state': 'no_go',
            'ceo_decision_comment': self.motif,
        })
        self.annonce_id.message_post(
            body=f"❌ NO GO — Motif : {self.motif}",
            message_type='notification',
            partner_ids=[self.annonce_id.user_id.partner_id.id]
        )