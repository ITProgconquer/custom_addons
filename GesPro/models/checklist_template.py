from odoo import models, fields


class ChecklistTemplate(models.Model):
    _name = "gespro.checklist.template"
    _description = "Modèle de checklist"
    _order = "category, sequence"

    name = fields.Char(
        string="Libellé",
        required=True,
        unique=True
    )

    category = fields.Selection([
        ('tech', 'Technique'),
        ('admin', 'Administratif'),
        ('fin', 'Financier'),
    ], string="Catégorie", required=True)

    description = fields.Text(string="Description détaillée")

    sequence = fields.Integer(string="Ordre", default=10)

    active = fields.Boolean(string="Actif", default=True)

    is_mandatory = fields.Boolean(
        string="Bloquant pour la soumission",
        default=True
    )