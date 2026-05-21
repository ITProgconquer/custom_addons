from odoo import models, fields


class ChecklistTemplate(models.Model):
    _name = "gespro.checklist.template"
    _description = "Modèle de checklist"
    _order = "category, sequence"

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Ce libellé existe déjà. Il doit être unique.'),
    ]

    name = fields.Char(
        string="Libellé",
        required=True
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