from odoo import models, fields


class ChecklistLine(models.Model):
    _name = "gespro.checklist.line"
    _description = "Item de checklist d'un appel"
    _order = "categorie, sequence"

    appel_id = fields.Many2one(
        'gespro.appel',
        string="Appel à Concurrence",
        required=True,
        ondelete='cascade'
    )

    template_id = fields.Many2one(
        'gespro.checklist.template',
        string="Modèle source",
        required=True
    )

    categorie = fields.Selection([
        ('tech', 'Technique'),
        ('admin', 'Administratif'),
        ('fin', 'Financier'),
    ], string="Catégorie", required=True)

    libelle = fields.Char(string="Description de l'item", required=True)

    is_done = fields.Boolean(
        string="Réalisé",
        default=False,
        tracking=True
    )

    responsible_id = fields.Many2one(
        'res.users',
        string="Responsable"
    )

    note = fields.Text(string="Observation")

    sequence = fields.Integer(string="Ordre", default=10)

    is_mandatory = fields.Boolean(
        string="Bloquant",
        default=True
    )