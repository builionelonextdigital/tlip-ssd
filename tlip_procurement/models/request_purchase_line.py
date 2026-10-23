from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class RequestPurchaseLine(models.Model):
    _name = "request.purchase.line"
    _description = "Procurement Request Line"
    _order = 'request_id, id'
    _rec_name = 'product_categ_id'

    user_id = fields.Many2one(related='request_id.user_id', string='Applicant')
    request_id = fields.Many2one(
        comodel_name='request.purchase',
        string='Reference',
        index=True, ondelete='cascade',
        required=True
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Goods/Service',
        domain=[('purchase_ok', '=', True)]
    )
    product_categ_id = fields.Many2one(
        comodel_name='product.category',
        string="Category",
        required=True
    )
    description = fields.Text(string="Description", required=True)
    project_id = fields.Many2one('development.project')
    development_phase_id = fields.Many2one('development.phase', string="Phase")
    qty_demand = fields.Float(
        string="Demand", required=True,
        digits='Product Unit of Measure',
        default=1
    )
    price_unit = fields.Float(
        string='Unit Price', required=True,
        compute="_compute_price_unit", store=True, readonly=False, digits='Product Price')
    available_product_uom_ids = fields.Many2many(
        'uom.uom', compute='_compute_available_product_uom_ids')
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string="UoM",
        required=True
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Budget Code',
        required=True
    )
    price_total = fields.Monetary(
        compute='_compute_amount', string="Amount", store=True)
    contract_total = fields.Monetary(string="Contract Amount")
    company_id = fields.Many2one(
        related='request_id.company_id',
        store=True, readonly=True
    )
    currency_id = fields.Many2one(
        related='request_id.currency_id',
        store=True, readonly=True
    )
    state = fields.Selection(related='request_id.state', store=True)
    request_type = fields.Selection(
        related='request_id.request_type', store=True)
    vendor_id = fields.Many2one(related='request_id.vendor_id')
    date_order = fields.Date(related='request_id.date_order')
    date_planned = fields.Date(related='request_id.date_planned')
    budget_department_id = fields.Many2one(
        related='request_id.budget_department_id')
    budget_department_group_id = fields.Many2one(
        "budget.department.group", related="budget_department_id.department_group_id"
    )
    matching_number = fields.Char(
        string="Matching #",
        copy=False, index='btree'
    )
    task_id = fields.Many2one(
        comodel_name="procurement.task", readonly=True,
        string="Procurement Task"
    )
    invoice_lines = fields.One2many(
        'account.move.line', 'request_purchase_line_id', string="Bill Lines",
        readonly=True, copy=False)
    required_project = fields.Boolean(compute="_compute_required_project")
    contract_currency_id = fields.Many2one(comodel_name='res.currency')
    budget_reserved_id = fields.Many2one(
        comodel_name='budget.reserved', string='Budget Reserved')

    @api.depends('product_id')
    def _compute_available_product_uom_ids(self):
        for record in self:
            if record.product_id:
                uoms = self.env['uom.uom'].search(
                    [('category_id', '=', record.product_id.uom_id.category_id.id)])
            else:
                uoms = self.env['uom.uom'].search([])
            record.available_product_uom_ids = [(6, 0, uoms.ids)]

    @api.depends('qty_demand', 'price_unit')
    def _compute_amount(self):
        for line in self:
            line.price_total = line.qty_demand * line.price_unit

    @api.depends("product_id")
    def _compute_price_unit(self):
        for rec in self:
            rec.price_unit = rec.product_id.standard_price

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            product = line.product_id
            line.product_uom_id = product.uom_po_id

            if product:
                line.product_categ_id = product.categ_id
                line.description = product.name

    @api.depends('analytic_account_id')
    def _compute_required_project(self):
        for rec in self:
            required_project = False
            if rec.analytic_account_id and rec.analytic_account_id.code.startswith('IN'):
                required_project = True
            rec.required_project = required_project

    def _calculate_matching_key(self):
        matching = False
        if self.vendor_id:
            matching = self.vendor_id
        elif self.product_id.seller_ids:
            matching = self.product_id.seller_ids[0].partner_id
        elif self.product_id:
            matching = self.product_id
        elif self.product_categ_id:
            matching = self.product_categ_id

        return matching

    @api.model
    def _assign_matching_numnber(self, group_mapping):
        RequestLine = self.env["request.purchase.line"]
        for matching_key, lines in group_mapping.items():
            lines = RequestLine.concat(*lines)
            lines.write({"matching_number": matching_key.display_name})

    def action_suggest_group_procurement_task(self):
        group_mapping = {}
        for line in self:
            matching_key = line._calculate_matching_key()
            group_mapping.setdefault(matching_key, []).append(line)

        self._assign_matching_numnber(group_mapping)
        return self._action_open_groupby_collections()

    def action_assign_procurement_task(self):
        assigned_tasks = self.filtered(lambda line: line.task_id)
        if assigned_tasks:
            raise ValidationError(
                _(f"Procurement {', '.join(assigned_tasks.mapped('request_id.name'))} has been assigned task"))
        if len(self.mapped('company_id')) > 1:
            raise ValidationError(
                _("Only allow to create task for collections with same company")
            )
        if len(self.mapped('budget_department_group_id')) > 1:
            raise ValidationError(
                _(
                    "Only allow to create task for collections with same budget department group"
                )
            )
        total_amount = sum(self.mapped("price_total"))
        select_bidding = ''
        if float_compare(total_amount, self.env.company.minimum_biding_amount, 0) == 1:
            select_bidding = 'bidding'
        ctx = dict(self.env.context)
        procurement_group = self.env.ref(
            'tlip_access_rights.group_tlip_procurement_user')
        user_ids = procurement_group.users.ids
        ctx.update({
            "default_request_line_ids": [(6, 0, self.ids)],
            "default_date_order": min(self.mapped("date_order")),
            "default_date_planned": min(self.mapped("date_planned")),
            "default_select_bidding": select_bidding,
            "hidden_bidding": True if not select_bidding else False,
            "default_procurement_user_ids": [(6, 0, user_ids)],
            "default_company_id": self.company_id.id,
        })
        return {
            'name': 'Assign Task',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'res_model': 'procurement.task',
            'views': [(self.env.ref('tlip_procurement.procurement_assign_task_view_form').id, 'form')],
            'context': ctx
        }

    def _action_open_groupby_collections(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            'tlip_procurement.request_procurement_collection_action')
        action['context'] = {
            'search_default_group_by_matching': True, 'search_default_group_by_budget_department_group': True, 'expand': True}
        action['domain'] = [('id', 'in', self.ids)]
        action['target'] = 'main'
        action['name'] = 'Suggest Group'
        return action

    def action_view_budget_code_info(self):
        self.ensure_one()
        budget_line = self.env['budget.line.year'].search([('account_id', '=', self.analytic_account_id.id),
                                                           ('budget_year_id.state', '=', 'confirmed'),
                                                           ('company_id', '=', self.company_id.id)], limit=1)
        
        return {
            'name': 'Budget Code Info',
            'view_mode': 'form',
            'view_id': self.env.ref('tlip_account.budget_line_year_simple_view_form').id,
            'view_type': 'form',
            'res_model': 'budget.line.year',
            'res_id': budget_line.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': dict(self.env.context) or {}
        }
