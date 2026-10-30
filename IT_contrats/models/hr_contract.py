from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrContractCustom(models.Model):
    _name = "hr.contract.custom"
    _description = "Contrat employé"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date_start desc"

    # Référence
    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default="Nouveau"
    )

    # Employé
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employé",
        required=True,
        tracking=True
    )

    # Dates
    date_start = fields.Date(
        string="Date de début",
        required=True,
        tracking=True
    )
    date_end = fields.Date(
        string="Date de fin",
        tracking=True
    )

    # Type de contrat
    contract_type = fields.Selection([
        ('cdi', 'CDI'),
        ('cdd', 'CDD'),
        ('stage', 'Stage'),
        ('consultant', 'Consultant'),
    ], string="Type de contrat", required=True, default='cdi', tracking=True)

    # Quotas
    annual_quota = fields.Float(
        string="Quota congés annuels (jours)",
        default=30.0,
        required=True
    )
    absence_quota = fields.Float(
        string="Quota absences (jours)",
        default=10.0,
        required=True
    )

    # État
    state = fields.Selection([
        ('actif', 'Actif'),
        ('termine', 'Terminé'),
    ], string="Statut", default='actif', tracking=True)

    # Notes
    note = fields.Text(string="Notes RH")

    # Relation vers les comptes congés
    # leave_account_ids = fields.One2many(
    #     'hr.leave.account',
    #     'contract_id',
    #     string="Comptes Congés"
    # )

    # ─── MÉTHODES ───────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.contract.custom')
        return super().create(vals_list)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for record in self:
            if record.date_end and record.date_start:
                if record.date_end < record.date_start:
                    raise ValidationError(
                        "La date de fin ne peut pas être antérieure à la date de début."
                    )

    def action_terminer(self):
        self.ensure_one()
        self.state = 'termine'
        self.message_post(body=f"📋 Contrat terminé par {self.env.user.name}")

    def action_reactiver(self):
        self.ensure_one()
        self.state = 'actif'
        self.message_post(body=f"✅ Contrat réactivé par {self.env.user.name}")

    @api.model
    def _compute_quota_for_year(self, employee, year):
        """Calcule le quota au prorata selon la date de début du contrat"""
        contract = self.search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'actif'),
            ('date_start', '<=', f'{year}-12-31'),
        ], limit=1)

        if not contract:
            return 0

        year_start = fields.Date.from_string(f'{year}-01-01')
        year_end = fields.Date.from_string(f'{year}-12-31')

        # Si le contrat commence après l'année → 0
        if contract.date_start > year_end:
            return 0

        # Si le contrat se termine avant le début de l'année → 0
        if contract.date_end and contract.date_end < year_start:
            return 0

        # Mois travaillés dans l'année
        effective_start = max(contract.date_start, year_start)
        effective_end = min(contract.date_end, year_end) if contract.date_end else year_end
        days_worked = (effective_end - effective_start).days + 1
        months_worked = days_worked / 30.0

        return min(months_worked * 2.5, contract.annual_quota)