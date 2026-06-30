from odoo import models, fields

class AnnulerAppelWizard(models.TransientModel):
    _name = "gespro.appel.annuler.wizard"
    _description = "Assistant d'annulation d'un Appel à Concurrence"

    appel_id = fields.Many2one('gespro.appel', string="Appel à Concurrence", required=True, readonly=True)
    motif = fields.Text(string="Motif de l'annulation", required=True)

    def action_confirm_annuler(self):
        self.ensure_one()
        appel = self.appel_id
        # Enregistrer le motif
        appel.motif_annulation = self.motif
        # Changer l'état
        appel.state = 'annule'
        # Message dans le chatter
        appel.message_post(body=f"❌ Appel à Concurrence annulé par {self.env.user.name}. Motif : {self.motif}")
        # Envoi de l'email à tout le monde (sauf expéditeur/admin)
        template = self.env.ref('GesPro.mail_template_appel_annuler', raise_if_not_found=False)
        if template:
            emails = self.env['gespro.annonce']._get_all_gespro_emails(exclude_user=self.env.user)
            if emails:
                template.send_mail(
                    appel.id,
                    force_send=True,
                    email_values={'email_to': emails}
                )
        return {'type': 'ir.actions.act_window_close'}