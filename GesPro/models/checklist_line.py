from odoo import models, fields
from odoo.exceptions import AccessError


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
        default=False
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
    def write(self, vals):
        for line in self:
            user = self.env.user
            # CEO peut tout faire
            if user.has_group('GesPro.group_ceo'):
                continue
            # PM : interdit de modifier les checklists
            if user.has_group('GesPro.group_pm'):
                raise AccessError("Le PM ne peut pas modifier les checklists.")
            # TECH : uniquement tech
            if user.has_group('GesPro.group_tech') and line.categorie != 'tech':
                raise AccessError("Vous ne pouvez modifier que les checklists techniques.")
            # FIN : uniquement fin
            if user.has_group('GesPro.group_fin') and line.categorie != 'fin':
                raise AccessError("Vous ne pouvez modifier que les checklists financières.")
            # RESADMIN : uniquement admin
            if user.has_group('GesPro.group_resadmin') and line.categorie != 'admin':
                raise AccessError("Vous ne pouvez modifier que les checklists administratives.")
        return super().write(vals)