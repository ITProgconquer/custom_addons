from odoo import models, fields


class CvPersonnel(models.Model):
    _name = "gespro.cv_personnel"
    _description = "CV du personnel"
    _order = "name"

    _sql_constraints = [
        ('matricule_unique', 'UNIQUE(matricule)', 'Ce matricule existe déjà. Il doit être unique.'),
    ]

    name = fields.Char(
        string="Nom et prénom",
        required=True
    )

    matricule = fields.Char(
        string="Matricule interne"
    )

    qualification = fields.Char(
        string="Diplôme principal ou poste",
        required=True
    )

    experience_years = fields.Integer(
        string="Années d'expérience",
        required=True
    )

    cv_file = fields.Binary(
        string="Fichier CV (PDF/DOCX)",
        required=True
    )
    cv_filename = fields.Char(string="Nom du fichier CV")

    specialties = fields.Text(
        string="Domaines d'expertise ou certifications"
    )

    active = fields.Boolean(string="Actif", default=True)

    user_id = fields.Many2one(
        'res.users',
        string="Créateur",
        default=lambda self: self.env.user
    )