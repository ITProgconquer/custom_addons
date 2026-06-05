from odoo import api, models, fields
from odoo.exceptions import AccessError


class ChecklistLine(models.Model):
    _name = "gespro.checklist.line"
    _description = "Item de checklist"
    _order = "categorie, sequence"

    appel_id = fields.Many2one('gespro.appel', required=True, ondelete='cascade')
    categorie = fields.Selection([
        ('tech', 'Technique'),
        ('admin', 'Administratif'),
        ('fin', 'Financier'),
    ], string="Catégorie", required=True)
    libelle = fields.Char("Tâche", required=True)
    responsible_id = fields.Many2one('res.users', string="Assigné à")
    note = fields.Text("Commentaire")
    sequence = fields.Integer("Ordre", default=10)


    state = fields.Selection([
        ('todo', 'À faire'),
        ('in_progress', 'En cours'),
        ('done', 'Terminé'),
    ], string="État", default='todo', tracking=True)


    
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
    
    
    @api.model_create_multi
    def create(self, vals_list):
        user = self.env.user
        for vals in vals_list:
            if user.has_group('GesPro.group_tech') and vals.get('categorie') != 'tech':
                raise AccessError("Vous ne pouvez créer que des tâches techniques.")
            if user.has_group('GesPro.group_fin') and vals.get('categorie') != 'fin':
                raise AccessError("Vous ne pouvez créer que des tâches financières.")
            if user.has_group('GesPro.group_resadmin') and vals.get('categorie') != 'admin':
                raise AccessError("Vous ne pouvez créer que des tâches administratives.")
        return super().create(vals_list)