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
        self.offre_id.state = 'no_go'
        self.offre_id.message_post(
            body=f"🔴 NO GO donné par {self.env.user.name}\nMotif : {self.motif}"
        )
        return {'type': 'ir.actions.act_window_close'}