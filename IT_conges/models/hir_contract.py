from odoo import models, fields

class HrContractCustom(models.Model):
    _inherit = "hr.contract.custom"

    leave_account_ids = fields.One2many(
        'hr.leave.account',
        'contract_id',
        string="Comptes Congés"
    )