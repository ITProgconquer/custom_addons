from odoo import models, fields

class AppelOffreIgnoreWizard(models.TransientModel):
    _name = "gespro.appel.offre.ignore.wizard"
    _description = "Assistant de refus d'un appel d'offre"

    offre_id = fields.Many2one(
        'gespro.appel.offre',
        string="Appel d'offre",
        required=True,
        readonly=True
    )

    motif = fields.Text(string="Motif du refus", required=True)

    def action_confirm_no_go(self):
        self.ensure_one()
        # Passage au statut NO GO et enregistrement du motif
        self.offre_id.write({
            'state': 'no_go',
            'ceo_comment': self.motif,
        })

        # Notification chatter
        partners = self.offre_id.pm_id.partner_id | self.offre_id.annonce_id.user_id.partner_id | self.env.user.partner_id
        self.offre_id.notify_users(
            partner_ids=partners.ids,
            body=f"L'appel d'offre {self.offre_id.name} a été refusé (NO GO). Motif : {self.motif}"
        )
        # Email à tout le monde
        template = self.env.ref('GesPro.mail_template_offre_nogo', raise_if_not_found=False)
        if template:
            emails = self.env['gespro.annonce']._get_all_gespro_emails(exclude_user=self.env.user)
            if emails:
                template.send_mail(
                    self.offre_id.id,
                    force_send=True,
                    email_values={'email_to': emails}
                )
        return {'type': 'ir.actions.act_window_close'}