from odoo import models, fields, api

class InvestigationWizard(models.TransientModel):
    _name = "gespro.appel.offre.investigation.wizard"
    _description = "Instructions pour l'investigation"

    offre_id = fields.Many2one('gespro.appel.offre', string="Appel d'offre", required=True, readonly=True)
    instructions = fields.Text(string="Instructions du CEO", required=True)

    def action_confirm_investigation(self):
        self.ensure_one()
        offre = self.offre_id
        offre.state = 'en_investigation'

        comment = self.instructions or ''
        body = f"🔍 Investigation demandée par {self.env.user.name} pour l'appel d'offre {offre.name}."
        if comment:
            body += f"\n📝 Instructions : {comment}"
        offre.message_post(body=body)

        # Sauvegarde temporaire du commentaire pour l'email
        offre.ceo_comment = comment

        # Envoi de l'email au RESADMIN (et CEO si souhaité)
        resadmin_users = self.env['res.users'].search([
            ('groups_id', 'in', [self.env.ref('GesPro.group_resadmin').id]),
            ('id', '!=', self.env.user.id),
            ('login', '!=', 'admin'),
        ])
        if resadmin_users:
            template = self.env.ref('GesPro.mail_template_investigation', raise_if_not_found=False)
            if template:
                template.send_mail(
                    offre.id,
                    force_send=True,
                    email_values={'email_to': ','.join(resadmin_users.mapped('email'))}
                )

        # Effacer le commentaire pour ne pas le conserver
        offre.ceo_comment = False
        return {'type': 'ir.actions.act_window_close'}