import logging
from datetime import date, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

_GRID_COLUMNS = 3
_CELL_WIDTH = 200
_CELL_HEIGHT = 220


class SignTicket(models.Model):
    _name = "sign.ticket"
    _description = "Sign Ticket"
    _inherit = ["mail.thread", "mail.activity.mixin", "pdf.signature.mixin"]
    _rec_name = "name"
    _order = "name desc"

    name = fields.Char(
        string="Ticket Reference",
        required=True,
        copy=False,
        readonly=True,
        default="New",
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)
    signing_type = fields.Selection(
        selection=[
            ("normal", "Normal"),
        ],
        string="Signing Type",
        required=True,
        default="normal",
        tracking=True,
    )
    document_type_id = fields.Many2one(
        comodel_name="sign.document.type",
        string="Document Type",
        tracking=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="PIC",
        default=lambda self: self.env.user,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    res_model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Related Model",
        compute="_compute_res_model_id",
        store=True,
        ondelete="set null",
        tracking=True,
    )
    res_model = fields.Char(
        related="res_model_id.model",
        string="Related Model Name",
        store=True,
        readonly=True,
    )
    res_domain = fields.Char(
        string="Domain",
        default="[]",
    )
    res_id = fields.Many2oneReference(
        string="Related Record",
        model_field="res_model",
        tracking=True,
    )
    deadline = fields.Date(
        compute="_compute_deadline",
        store=True,
        readonly=False,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
            ("withdraw", "Withdrawn"),
        ],
        string="Status",
        required=True,
        default="draft",
        tracking=True,
    )
    sign_document_ids = fields.One2many(
        comodel_name="sign.document",
        inverse_name="ticket_id",
        string="Documents",
    )
    signer_line_ids = fields.One2many(
        comodel_name="sign.ticket.signer",
        inverse_name="ticket_id",
        string="Signers",
    )
    current_signer_id = fields.Many2one(
        comodel_name="sign.ticket.signer",
        string="Current Signer",
        compute="_compute_current_signer_id",
    )
    is_allow_to_approve_reject = fields.Boolean(
        compute="_compute_is_allow_to_approve_reject",
        string="Can Approve/Reject",
    )
    use_cell_positioning = fields.Boolean(
        related="document_type_id.use_cell_positioning"
    )
    placeholder_text = fields.Char(
        related="document_type_id.placeholder_text", store=False
    )
    note = fields.Text(string="Note")
    reference = fields.Char(string='Reference', compute='_compute_reference', readonly=True, store=False)

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.constrains("res_model_id", "res_id", "state")
    def _check_duplicate_esign_ticket(self):
        for record in self:
            if not record.res_model or not record.res_id or record.state in ["cancelled", "approved"]:
                continue

            duplicate = self.sudo().search([
                ("id", "!=", record.id),
                ("res_model", "=", record.res_model),
                ("res_id", "=", record.res_id),
                ("state", "not in", ["cancelled", "approved"]),
            ], limit=1)
            if duplicate:
                raise UserError(
                    _(
                        "An active E-Sign ticket already exists for this record: %s."
                    )
                    % duplicate.name
                )

    @api.depends("signer_line_ids", "state")
    def _compute_current_signer_id(self):
        waiting_state = self.env["sign.ticket.signer"]._get_waiting_state()
        for record in self:
            if record.state != "in_progress":
                record.current_signer_id = False
                continue
            current = record.signer_line_ids.filtered(
                lambda l: l.state in waiting_state
            )
            record.current_signer_id = current[:1].id if current else False

    @api.depends('res_model', 'res_id')
    def _compute_reference(self):
        for res in self:
            res.reference = "%s,%s" % (res.res_model, res.res_id)

    @api.depends("signer_line_ids.user_id", "signer_line_ids.state", "state")
    def _compute_is_allow_to_approve_reject(self):
        waiting_state = self.env["sign.ticket.signer"]._get_waiting_state()
        for record in self:
            record.is_allow_to_approve_reject = record.state == "in_progress" and any(
                line.user_id == self.env.user and line.state in waiting_state
                for line in record.signer_line_ids
            )

    @api.depends("document_type_id", "document_type_id.deadline_days")
    def _compute_deadline(self):
        for record in self:
            days = record.document_type_id.deadline_days
            if days:
                record.deadline = date.today() + timedelta(days=days)
            else:
                record.deadline = record.deadline

    @api.depends("document_type_id")
    def _compute_res_model_id(self):
        for record in self:
            record.res_model_id = (
                record.document_type_id.model_id or record.res_model_id
            )

    @api.onchange("document_type_id")
    def _onchange_document_type_id(self):
        if self.document_type_id and self.document_type_id.model_id:
            self.res_model_id = self.document_type_id.model_id
        else:
            self.res_model_id = False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @api.model
    def _get_signature_cell_box(self):
        return {
            "width": 60 if self.use_cell_positioning else 30,
            "height": _CELL_HEIGHT,
        }

    def _get_ticket_name(self, sequence_code, document_type):
        sequence = self.env["ir.sequence"].next_by_code(sequence_code)
        name_list = [document_type.code, sequence]
        return "/".join(filter(None, name_list))

    def _validate_signer(self, user=None):
        """Return the current user's waiting signer line, or raise UserError."""
        self.ensure_one()
        waiting_state = self.env["sign.ticket.signer"]._get_waiting_state()
        domain = [("state", "in", waiting_state)]
        if user is not None:
            domain += [("user_id", "=", user.id)]
        signer = self.signer_line_ids.filtered_domain(domain)
        if not signer:
            raise UserError(
                _("You are not allowed to approve or reject ticket %s.", self.name)
            )
        return signer

    def _is_valid_sign_document(self, document, signature_placeholders):
        """Check that a PDF document contains all required signature placeholders.

        :param document: sign.document record.
        :param signature_placeholders: list of placeholder strings, e.g. ['[signer1]', '[signer2]'].
        :return: True if all placeholders are found, False otherwise.
        :raises UserError: if the PDF cannot be read.
        """
        if not document.is_pdf:
            return True

        try:
            missing = self.search_placeholders_in_pdf(
                document._get_pdf_bytes(), signature_placeholders
            )
        except Exception as e:
            _logger.error(
                "Failed to validate placeholders in '%s': %s", document.filename, e
            )
            raise UserError(
                _(
                    "Failed to read the PDF document '%s'. It may be corrupted or in an unsupported format."
                )
                % document.filename
            )
        return not missing

    def _check_sign_documents(self):
        """Verify that every document contains the required signer placeholders.

        Each signer line contributes a placeholder based on its line_number,
        e.g. line_number=1 → '[signer1]'.  All PDF documents must contain
        every placeholder before the ticket can be submitted.

        :return: True if all documents are valid.
        :raises UserError: if any document is missing a placeholder.
        """
        self.ensure_one()
        document_type = self.document_type_id
        if not self.signer_line_ids and self.use_cell_positioning:
            return True

        if self.use_cell_positioning and not document_type.placeholder_text:
            raise UserError(
                _("Placeholder text in '%s' is required when using cell positioning.")
                % document_type.name
            )

        if self.use_cell_positioning:
            signature_placeholders = [document_type.placeholder_text]
        else:
            signature_placeholders = [
                f"[signer{line.line_number}]" for line in self.signer_line_ids
            ]

        for document in self.sign_document_ids:
            missing = [
                p
                for p in signature_placeholders
                if not self._is_valid_sign_document(document, [p])
            ]
            if missing:
                raise UserError(
                    _(
                        "Document '%(filename)s' is missing the following signature placeholder(s): %(placeholders)s.",
                        filename=document.filename,
                        placeholders=", ".join(missing),
                    )
                )
        return True

    def _validate_action_submit(self):
        self.ensure_one()
        if (
            not self.env.context.get("skip_signer_validation")
            and not self.signer_line_ids
        ):
            raise UserError(
                _("At least one signer is required before submitting the ticket.")
            )
        if not self.sign_document_ids:
            raise UserError(
                _("At least one document is required before submitting the ticket.")
            )
        self._check_sign_documents()

    def _action_sign(self):
        self.ensure_one()
        my_signer = self._validate_signer(user=self.env.user)
        my_signer.action_sign()
        if all(line.state == "signed" for line in self.signer_line_ids):
            self.write({"state": "approved"})
            self.sign_document_ids._clear_original_file()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_submit(self):
        for record in self:
            record._validate_action_submit()
            record.signer_line_ids._reset_status()
            record.sign_document_ids._restore_original()
            record.write({"state": "in_progress"})

    def action_approve(self):
        for record in self:
            if not record.is_allow_to_approve_reject:
                continue
            record._action_sign()
        return True

    def action_multi_approve_approval(self):
        return self.action_approve()

    def action_reject(self):
        self.ensure_one()
        signer = self._validate_signer(user=self.env.user)
        return {
            "type": "ir.actions.act_window",
            "name": _("Reject Ticket"),
            "res_model": "sign.ticket.reject.wizard",
            "views": [
                (
                    self.env.ref(
                        "pcv_sign_ticket.view_sign_ticket_reject_wizard_form"
                    ).id,
                    "form",
                )
            ],
            "target": "new",
            "context": {
                "default_ticket_id": self.id,
                "default_signer_id": signer.id,
            },
        }

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_withdraw(self):
        self.write({"state": "withdraw"})

    def action_reset_to_draft(self):
        self.write({"state": "draft"})
        self.mapped("sign_document_ids")._restore_original()

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------

    def write(self, vals):
        if "user_id" in vals and not self.env.user.has_group(
            "pcv_sign_ticket.group_sign_ticket_admin"
        ):
            raise UserError(_("Only E-Sign Admins can reassign the PIC."))
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                document_type = self.env["sign.document.type"].browse(
                    vals.get("document_type_id")
                )
                sequence_code = "pcv.sign.ticket.hard.copy"
                vals["name"] = (
                    self._get_ticket_name(sequence_code, document_type) or "New"
                )
        return super().create(vals_list)

    def _find_keyword_coordinate(self, keyword, pdf_bytes):
        if not self.use_cell_positioning:
            return super()._find_keyword_coordinate(keyword, pdf_bytes)

        document_type = self.document_type_id
        if not document_type.placeholder_text:
            raise UserError(
                _("Placeholder text in '%s' is required when using cell positioning.")
                % document_type.name
            )

        line_number = self.env.context.get("cell_position", 1)
        coordinate = super()._find_keyword_coordinate(
            document_type.placeholder_text, pdf_bytes
        )
        if not coordinate:
            return None

        row = (line_number - 1) // _GRID_COLUMNS
        col = (line_number - 1) % _GRID_COLUMNS

        x = coordinate["x"] + col * _CELL_WIDTH
        y = coordinate["y"] - row * _CELL_HEIGHT

        return {**coordinate, "x": x, "y": y}
