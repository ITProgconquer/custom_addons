from odoo import models, fields


class PersonnelLine(models.Model):
    _name = "gespro.personnel_line"
    _description = "Exigences en personnel pour un lot"

    lot_id = fields.Many2one(
        'gespro.lot',
        string="Lot",
        required=True,
        ondelete='cascade'
    )

    role = fields.Char(string="Poste / Fonction exigé", required=True)

    qualification_min = fields.Char(string="Qualification minimum", required=True)

    nb_exige = fields.Integer(string="Nombre exigé", required=True)

    experience_years = fields.Integer(string="Années d'expérience requises", required=True)

    experience_similar = fields.Text(string="Expérience projets similaires")

    certificates_required = fields.Text(string="Documents et certificats à fournir")

    is_satisfied = fields.Boolean(string="Satisfait", default=False, tracking=True)