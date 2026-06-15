from odoo import models, fields

class ResultatWizard(models.TransientModel):
    _name = "gespro.resultat.wizard"
    _description = "Enregistrer le résultat"

    appel_id = fields.Many2one('gespro.appel', string="Appel", required=True, readonly=True)
    resultat = fields.Selection([
        ('gagne', 'Gagné'),
        ('perdu', 'Perdu'),
    ], string="Résultat", required=True)
    capture = fields.Binary(string="Capture du résultat")
    capture_filename = fields.Char(string="Nom du fichier")

    def action_confirm(self):
        self.ensure_one()
        self.appel_id.write({
            'state': self.resultat,
            'resultat_capture': self.capture,
            'resultat_filename': self.capture_filename,
        })
        self.appel_id.message_post(body=f"📊 Résultat : {'🎉 Gagné' if self.resultat == 'gagne' else '😞 Perdu'}")
        return {'type': 'ir.actions.act_window_close'}