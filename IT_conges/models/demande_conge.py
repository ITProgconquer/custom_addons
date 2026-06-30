from odoo import models, fields, api
from odoo.exceptions import UserError

class DemandeConge(models.Model):
    _name = "gespro.demande.conge"
    _description = "Demande de congé"
    _inherit = ['mail.thread']
    _order = "date_demande desc"

    name = fields.Char(string="Référence", readonly=True, default="Nouveau")
    employee_id = fields.Many2one('res.users', string="Employé", default=lambda self: self.env.user, required=True, readonly=True)
    date_debut = fields.Date(string="Date de début", required=True)
    date_fin = fields.Date(string="Date de fin", required=True)
    nb_jours = fields.Integer(string="Nombre de jours", compute='_compute_nb_jours', store=True)
    motif = fields.Text(string="Motif")
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('approuve', 'Approuvé'),
        ('refuse', 'Refusé'),
    ], string="Statut", default='draft', tracking=True)
    date_demande = fields.Datetime(string="Date de demande", default=fields.Datetime.now, readonly=True)

    @api.depends('date_debut', 'date_fin')
    def _compute_nb_jours(self):
        for rec in self:
            if rec.date_debut and rec.date_fin:
                delta = (rec.date_fin - rec.date_debut).days + 1
                rec.nb_jours = delta
            else:
                rec.nb_jours = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('gespro.demande.conge')
        return super().create(vals_list)

    def action_soumettre(self):
        self.ensure_one()
        quota = self.env['gespro.quota.conge']._get_quota_employee(self.employee_id)
        total_pris = self.env['gespro.demande.conge'].search_count([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'approuve'),
            ('date_debut', '>=', fields.Date.today().replace(month=1, day=1)),
        ])
        if total_pris + self.nb_jours > quota:
            raise UserError(f"Quota insuffisant. Quota annuel : {quota} jours. Déjà pris : {total_pris} jours.")
        self.state = 'soumis'
        self.message_post(body=f"📨 Demande soumise par {self.employee_id.name}")

    def action_approuver(self):
        self.ensure_one()
        self.state = 'approuve'
        self.message_post(body=f"✅ Congé approuvé par {self.env.user.name}")

    def action_refuser(self):
        self.ensure_one()
        self.state = 'refuse'
        self.message_post(body=f"❌ Congé refusé par {self.env.user.name}")