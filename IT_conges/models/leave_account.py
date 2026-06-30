from odoo import models, fields, api

class LeaveAccount(models.Model):
    _name = "hr.leave.account"
    _description = "Compte congés employé"

    employee_id = fields.Many2one('hr.employee', string="Employé", required=True)
    year = fields.Integer(string="Année", required=True, default=lambda self: fields.Date.today().year)
    policy_id = fields.Many2one('hr.leave.policy', string="Politique")
    annual_quota = fields.Float(string="Quota annuel", default=30)
    carried_forward = fields.Float(string="Report N-1", default=0)
    acquired_days = fields.Float(string="Jours acquis", default=0)
    used_days = fields.Float(string="Jours utilisés", compute='_compute_used', store=True)
    remaining_days = fields.Float(string="Jours restants", compute='_compute_remaining', store=True)
    nb_demandes = fields.Integer(string="Nb demandes", compute='_compute_stats', store=True)
    nb_annuel = fields.Integer(string="Congés annuels", compute='_compute_stats', store=True)
    nb_maladie = fields.Integer(string="Maladie", compute='_compute_stats', store=True)
    nb_sans_solde = fields.Integer(string="Sans solde", compute='_compute_stats', store=True)
    dernier_conge = fields.Date(string="Dernier congé", compute='_compute_stats', store=True)
    prochain_conge = fields.Date(string="Prochain congé", compute='_compute_stats', store=True)
    absence_quota = fields.Integer(string="Quota absence (jours)", default=10)
    absence_used = fields.Float(string="Absences utilisées", compute='_compute_absence_used', store=True)
    absence_remaining = fields.Float(string="Absences restantes", compute='_compute_absence_remaining', store=True)


    status = fields.Selection([
        ('active', 'Actif'),
        ('blocked', 'Bloqué'),
    ], default='active')

    status_employe = fields.Selection([
        ('actif', 'Actif'),
        ('en_conge', 'En congé'),
        ('absence', 'Absent'),
    ], string="État",default='actif')



    @api.depends('employee_id')
    def _compute_used(self):
        today = fields.Date.today()
        for acc in self:
            requests = self.env['hr.leave.request'].search([
                ('employee_id', '=', acc.employee_id.id),
                ('state', '=', 'approved'),
                ('date_from', '>=', f'{acc.year}-01-01'),
                ('date_from', '<=', today),  # A déjà commencé
            ])
            used = 0
            for req in requests:
                start = req.date_from
                end = min(req.date_to, today)
                used += (end - start).days + 1
            acc.used_days = used


    @api.depends('annual_quota', 'carried_forward', 'acquired_days', 'used_days')
    def _compute_remaining(self):
        for acc in self:
            acc.remaining_days = acc.annual_quota + acc.carried_forward + acc.acquired_days - acc.used_days

    
    def _cron_allocate_annual(self):
        year = fields.Date.today().year
        employees = self.env['hr.employee'].search([])
        for emp in employees:
            if not self.search([('employee_id', '=', emp.id), ('year', '=', year)]):
                self.create({'employee_id': emp.id, 'year': year, 'annual_quota': 30, 'absence_quota': 10})

    
    @api.depends('employee_id')
    def _compute_stats(self):
        for acc in self:
            requests = self.env['hr.leave.request'].search([
                ('employee_id', '=', acc.employee_id.id),
                ('state', '=', 'approved'),
                ('date_from', '>=', f'{acc.year}-01-01'),
                ('date_to', '<=', f'{acc.year}-12-31'),
            ])
            acc.nb_demandes = len(requests)
            acc.nb_annuel = len(requests.filtered(lambda r: r.type_conge == 'annuel'))
            acc.nb_maladie = len(requests.filtered(lambda r: r.type_conge == 'maladie'))
            acc.nb_sans_solde = len(requests.filtered(lambda r: r.type_conge == 'sans_solde'))
            acc.dernier_conge = requests[-1].date_to if requests else False
            future = requests.filtered(lambda r: r.date_from >= fields.Date.today())
            acc.prochain_conge = future[0].date_from if future else False


    # @api.depends('employee_id')
    # def _compute_status_employe(self):
    #     for acc in self:
    #         today = fields.Date.today()
    #         conge = self.env['hr.leave.request'].search([
    #             ('employee_id', '=', acc.employee_id.id),
    #             ('state', '=', 'approved'),
    #             ('date_from', '<=', today),
    #             ('date_to', '>=', today),
    #         ], limit=1)
    #         if conge:
    #             acc.status_employe = 'en_conge'
    #         else:
    #             acc.status_employe = 'actif'


    @api.depends('employee_id')
    def _compute_absence_used(self):
        today = fields.Date.today()
        for acc in self:
            requests = self.env['hr.leave.request'].search([
                ('employee_id', '=', acc.employee_id.id),
                ('state', '=', 'approved'),
                ('imputation', '=', 'absence'),
                ('date_from', '>=', f'{acc.year}-01-01'),
                ('date_from', '<=', today),
            ])
            used = 0
            for req in requests:
                start = req.date_from
                end = min(req.date_to, today)
                used += (end - start).days + 1
            acc.absence_used = used

    
    @api.depends('absence_used', 'absence_quota')
    def _compute_absence_remaining(self):
        for acc in self:
            acc.absence_remaining = acc.absence_quota - acc.absence_used 


    

    @api.model
    def cron_update_leave_status(self):
        today = fields.Date.today()
        accounts = self.search([])
        for account in accounts:
            leave = self.env['hr.leave.request'].search([
                ('employee_id', '=', account.employee_id.id),
                ('state', '=', 'approved'),
                ('date_from', '<=', today),
                ('date_to', '>=', today),
            ], limit=1)
            account.status_employe = 'en_conge' if leave else 'actif'
            account._compute_used()
            account._compute_absence_used()