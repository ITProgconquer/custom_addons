from odoo import models, fields

class LeavePolicy(models.Model):
    _name = "hr.leave.policy"
    _description = "Politique de congés"

    name = fields.Char(string="Nom", required=True)
    annual_quota = fields.Float(string="Quota annuel (jours)", required=True, default=30)
    max_carry_forward = fields.Float(string="Report max (jours)", default=5)
    approval_level = fields.Selection([
        ('manager', 'Manager'),
        ('manager_hr', 'Manager + RH'),
        ('manager_hr_dg', 'Manager + RH + DG'),
    ], string="Niveau d'approbation", default='manager')
    active = fields.Boolean(default=True)