from odoo import models, fields, api
from odoo.exceptions import ValidationError

class LeaveRequest(models.Model):
    _name = "hr.leave.request"
    _description = "Demande de congé"
    _inherit = ['mail.thread']
    _order = "date_from desc"

    name = fields.Char(string="Référence", readonly=True, default="Nouveau")
    employee_id = fields.Many2one('hr.employee', string="Employé", default=lambda self: self._get_employee(), required=True)
    date_from = fields.Date(string="Date début", required=True)
    date_to = fields.Date(string="Date fin", required=True)
    days_requested = fields.Float(string="Jours demandés", compute='_compute_days', store=True)
    remaining_days = fields.Float(string="Jours restants", compute='_compute_remaining_days', store=False)
    solde_color = fields.Char(string="Couleur solde", compute='_compute_remaining_days')

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('manager', 'Validation Manager'),
        ('hr', 'Validation RH'),
        ('approved', 'Approuvé'),
        ('refused', 'Refusé'),
    ], string="Statut", default='draft', tracking=True)
    note = fields.Text(string="Motif")

    type_conge = fields.Selection([
        ('annuel', 'Congé annuel'),
        ('maladie', 'Maladie'),
        ('maternite', 'Maternité'),
        ('paternite', 'Paternité'),
        ('sans_solde', 'Sans solde'),
        ('formation', 'Formation'),
        ('autre', 'Autre'),
    ], string="Type de congé", required=True, default='annuel')

    imputation = fields.Selection([
        ('conge_annuel', 'Congé annuel (30 jours)'),
        ('absence', 'Absence (10 jours)'),
    ], string="Imputation", required=True, default='conge_annuel')
    

    def _get_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)

    @api.depends('date_from', 'date_to')
    def _compute_days(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                rec.days_requested = (rec.date_to - rec.date_from).days + 1
            else:
                rec.days_requested = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.leave.request')
        return super().create(vals_list)

    def action_submit(self):
        self.ensure_one()
        account = self.env['hr.leave.account'].search([
            ('employee_id', '=', self.employee_id.id),
            ('year', '=', fields.Date.today().year),
        ], limit=1)
        if self.imputation == 'conge_annuel':
            if not account or account.remaining_days <= 0:
                raise ValidationError("Vous n'avez plus de jours de congé annuel.")
            if self.days_requested > account.remaining_days:
                raise ValidationError(f"Solde insuffisant. Restant : {account.remaining_days} jours.")
        elif self.imputation == 'absence':
            if not account or account.absence_remaining <= 0:
                raise ValidationError("Vous n'avez plus de jours d'absence.")
            if self.days_requested > account.absence_remaining:
                raise ValidationError(f"Solde absence insuffisant. Restant : {account.absence_remaining} jours.")
        self.state = 'manager'
        self.message_post(body=f"📨 Demande soumise par {self.employee_id.name}")


    def action_manager_approve(self):
        self.state = 'hr'

        

    def action_hr_approve(self):
        self.state = 'approved'
        account = self.env['hr.leave.account'].search([
            ('employee_id', '=', self.employee_id.id),
            ('year', '=', fields.Date.today().year),
        ], limit=1)
        if account:
            today = fields.Date.today()
            if self.date_from <= today <= self.date_to:
                account.status_employe = 'en_conge'
            account._compute_used()
            account._compute_remaining()



    def action_refuse(self):
        self.state = 'refused'
        self.message_post(body=f"❌ Congé refusé")


    @api.depends('employee_id')
    def _compute_remaining_days(self):
        for rec in self:
            account = self.env['hr.leave.account'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('year', '=', fields.Date.today().year),
            ], limit=1)
            rec.remaining_days = account.remaining_days if account else 0
            if rec.remaining_days <= 5:
                rec.solde_color = 'danger'
            elif rec.remaining_days <= 10:
                rec.solde_color = 'warning'
            else:
                rec.solde_color = 'success'