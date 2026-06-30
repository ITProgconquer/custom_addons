from odoo import api, models, fields, api

class QuotaConge(models.Model):
    _name = "gespro.quota.conge"
    _description = "Quota de congés annuel par employé"

    employee_id = fields.Many2one('res.users', string="Employé", required=True)
    annee = fields.Integer(string="Année", required=True, default=lambda: fields.Date.today().year)
    nb_jours_total = fields.Integer(string="Quota total (jours)", required=True, default=30)

    _sql_constraints = [
        ('unique_employee_year', 'UNIQUE(employee_id, annee)', 'Un quota existe déjà pour cet employé cette année.')
    ]

    def _get_quota_employee(self, employee):
        quota = self.search([
            ('employee_id', '=', employee.id),
            ('annee', '=', fields.Date.today().year)
        ], limit=1)
        return quota.nb_jours_total if quota else 30