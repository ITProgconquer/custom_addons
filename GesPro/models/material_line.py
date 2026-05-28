from odoo import models, fields


class MaterialLine(models.Model):
    _name = "gespro.material_line"
    _description = "Exigences en matériel pour un lot"

    lot_id = fields.Many2one(
        'gespro.lot',
        string="Lot",
        required=True,
        ondelete='cascade'
    )

    designation = fields.Char(string="Désignation du matériel", required=True)

    specifications = fields.Text(string="Spécifications techniques minimales")

    qty_required = fields.Integer(string="Quantité minimum exigée", required=True)

    qty_provided = fields.Integer(string="Quantité fournie")

    is_satisfied = fields.Boolean(string="Conformité validée", default=False)