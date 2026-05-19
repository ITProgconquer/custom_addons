from odoo import models, fields, api


class SimilarContract(models.Model):
    _name = "gespro.similar.contract"
    _description = "Marché similaire gagné"
    _order = "contract_date desc"

    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default="Nouveau"
    )

    appel_id = fields.Many2one(
        'gespro.appel',
        string="Appel source (optionnel)"
    )

    contract_date = fields.Date(
        string="Date d'attribution",
        required=True
    )

    contract_type = fields.Selection([
        ('acquisition', 'Acquisition matériels informatique'),
        ('cable_reseau', 'Travaux câblage réseau'),
        ('fibre_optique', 'Travaux fibre optique'),
        ('autre', 'Autre'),
    ], string="Type de marché", required=True)

    client_name = fields.Char(
        string="Organisme client",
        required=True
    )

    description = fields.Text(string="Résumé du marché")

    amount = fields.Float(
        string="Montant total",
        digits=(16, 2)
    )

    document = fields.Binary(string="Attestation ou dossier complet")
    document_filename = fields.Char(string="Nom du fichier")

    active = fields.Boolean(string="Actif", default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('gespro.similar.contract')
        return super().create(vals_list)