from odoo import models, fields, api


class Lot(models.Model):
    _name = "gespro.lot"
    _description = "Lot d'un appel à concurrence"

    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default="Nouveau"
    )

    appel_id = fields.Many2one(
        'gespro.appel',
        string="Appel à Concurrence",
        required=True,
        ondelete='cascade'
    )

    lot_num = fields.Integer(string="N° du lot", required=True)

    titre = fields.Char(string="Intitulé du lot", required=True)

    personnel_line_ids = fields.One2many(
        'gespro.personnel_line',
        'lot_id',
        string="Exigences en personnel"
    )

    material_line_ids = fields.One2many(
        'gespro.material_line',
        'lot_id',
        string="Exigences en matériel"
    )

    is_ready = fields.Boolean(
        string="Lot prêt",
        compute='_compute_is_ready',
        store=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('gespro.lot')
        return super().create(vals_list)

    @api.depends('personnel_line_ids.is_satisfied', 'material_line_ids.is_satisfied')
    def _compute_is_ready(self):
        for record in self:
            pers_ok = all(record.personnel_line_ids.mapped('is_satisfied')) if record.personnel_line_ids else True
            mat_ok = all(record.material_line_ids.mapped('is_satisfied')) if record.material_line_ids else True
            record.is_ready = pers_ok and mat_ok

    
    def action_open_lot(self):
        """Ouvre la fiche détaillée du lot avec Personnel et Matériel"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.titre,
            'res_model': 'gespro.lot',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }