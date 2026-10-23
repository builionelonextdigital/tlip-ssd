from odoo import api, fields, models, _


class ApprovalCategory(models.Model):
    _inherit = "approval.category"

    model_id = fields.Many2one(
        "ir.model", string="Model", domain=[("field_id", "!=", False)], required=True, ondelete="cascade",
        help="Model on which apply filter domain"
    )
    related_model = fields.Char(
        string="Related Model", related="model_id.model", store=True)
    approval_option_ids = fields.One2many(
        "approval.category.option", "category_id", string="Options")
    to_review_contract = fields.Boolean('Review Contract')

    def _compute_request_to_validate_count(self):
        domain = [('request_status', '=', 'pending'), ('approver_ids.user_ids', 'in', self.env.user.ids)]
        requests_data = self.env['approval.request']._read_group(domain, ['category_id'], ['__count'])
        requests_mapped_data = {category.id: count for category, count in requests_data}
        for category in self:
            category.request_to_validate_count = requests_mapped_data.get(category.id, 0)


class ApprovalCategoryApprover(models.Model):
    _inherit = 'approval.category.approver'

    category_id = fields.Many2one(
        'approval.category', string='Approval Type', ondelete='cascade', required=False)
    category_option_id = fields.Many2one(
        'approval.category.option', ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', ondelete='cascade', required=False,
                              check_company=True, domain="[]")
    job_id = fields.Many2one('hr.job', ondelete='cascade', string="Job Position")

    @api.depends('category_option_id')
    def _compute_existing_user_ids(self):
        for record in self:
            record.existing_user_ids = record.category_option_id.approver_ids.user_id


class ApprovalCategoryOptions(models.Model):
    _name = "approval.category.option"
    _description = "Approval Category Options"

    name = fields.Char("Description", required=True)
    filter_domain = fields.Char(
        string="Apply on",
        readonly=False, store=True
    )
    category_id = fields.Many2one("approval.category")
    related_model = fields.Char(
        string="Related Model", related="category_id.related_model", store=True)
    approval_minimum = fields.Integer(
        string="Minimum Approval", default=1, required=True)
    user_ids = fields.Many2many(
        'res.users', compute='_compute_user_ids', string="Approver Users")
    approver_ids = fields.One2many(
        'approval.category.approver', 'category_option_id', string="Approvers")
    approver_sequence = fields.Boolean(
        'Approvers Sequence?',
        help="If checked, the approvers have to approve in sequence (one after the other). If Employee's Manager is selected as approver, they will be the first in line.")

    @api.depends('approver_ids')
    def _compute_user_ids(self):
        for record in self:
            record.user_ids = record.approver_ids.user_id
