from odoo import models, fields, api

class Depouillement(models.Model):
    _name = "gespro.depouillement"
    _description = "Dépouillement d'un appel d'offre"
    _order = "ordre"

    appel_id = fields.Many2one(
        'gespro.appel',
        string="Appel d'offre",
        required=True,
        ondelete='cascade'
    )

    ordre = fields.Integer(string="Ordre", default=1)
    soumissionnaires = fields.Char(string="Soumissionnaires")
    lot_id = fields.Many2one(
        'gespro.lot',
        string="Lot",
        required=True,
        domain="[('appel_id', '=', appel_id)]"
    )
    lot_num = fields.Integer(string="Lot N°", related='lot_id.lot_num', readonly=True)
    montant_min_ttc = fields.Float(string="Montant minimum TTC")
    montant_max_ttc = fields.Float(string="Montant maximum TTC")
    observation = fields.Text(string="Observation")