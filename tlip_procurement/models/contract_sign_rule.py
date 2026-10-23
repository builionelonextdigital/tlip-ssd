from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class ContractSignRule(models.Model):
    _name = "contract.sign.rule"
    _description = "Contract Sign Rule"

    job_ids = fields.Many2many("hr.job", string="Job Position", required=True)
    contract_amount = fields.Float(string="Maximum Contract Amount", required=True)

    @api.constrains("contract_amount")
    def check_contract_amount(self):
        for record in self:
            if record.contract_amount < 0:
                raise ValidationError(_("The contract amount should be positive"))

    @api.model
    def get_rules_on_contract_amount(self, contract_amount):
        """
        Get the contract sign rules based on the contract amount.
        :param contract_amount: The contract amount to check.
        :return: A list of contract sign rules that match the given contract amount.
        """
        return self.search([("contract_amount", ">=", contract_amount)])
