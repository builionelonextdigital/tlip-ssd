from odoo import api, fields, models


class SignTicketMixin(models.AbstractModel):
    _name = "sign.ticket.mixin"
    _description = "Sign Ticket Mixin"

    sign_ticket_ids = fields.One2many(
        comodel_name="sign.ticket",
        inverse_name="res_id",
        string="Sign Tickets",
    )
    sign_ticket_count = fields.Integer(compute="_compute_sign_ticket_count")

    def _compute_sign_ticket_count(self):
        for record in self:
            record.sign_ticket_count = len(record.sign_ticket_ids)

    def action_generate_sign_ticket(self):
        tickets = self.env["sign.ticket"]
        for record in self:
            on_going_tickets = record.sign_ticket_ids.filtered(lambda t: t.state not in ["cancelled", "approved"])
            if not on_going_tickets:
                vals = record._prepare_sign_ticket_vals()
                tickets |= self.env["sign.ticket"].create(vals)
            else:
                tickets |= on_going_tickets
        return self._action_open_sign_ticket(tickets)

    def action_open_sign_ticket(self):
        self.ensure_one()
        return self._action_open_sign_ticket(self.sign_ticket_ids)

    def _get_sign_ticket_document_type(self):
        self.ensure_one()
        model_id = self.env["ir.model"]._get_id(self._name)
        document_type = self.env["sign.document.type"].search(
            [("model_id", "=", model_id)],
            limit=1,
        )
        if not document_type:
            document_type = self.env["sign.document.type"].search(
                [("model_id", "=", False)],
                limit=1,
            )
        return document_type

    def _prepare_sign_ticket_document_vals(self):
        return []

    def _prepare_sign_ticket_vals(self, company_id=None):
        self.ensure_one()
        document_type = self._get_sign_ticket_document_type()
        if company_id is None:
            company_id = getattr(self, "company_id", None)
        if not company_id:
            raise ValueError("Missing company_id for request sign ticket.")

        return {
            "document_type_id": document_type.id,
            "company_id": company_id.id,
            "res_model_id": self.env["ir.model"]._get_id(self._name),
            "res_id": self.id,
            "sign_document_ids": self._prepare_sign_ticket_document_vals(),
        }

    def _action_open_sign_ticket(self, tickets):
        action = self.env['ir.actions.act_window']._for_xml_id('pcv_sign_ticket.action_sign_ticket')
        action.update({
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
            },
            "domain": [("res_id", "in", self.ids), ("res_model", "=", self._name)]
        })

        if len(tickets) == 1:
            action.update({
                "res_id": tickets.id,
                "view_mode": "form",
                "views": [(self.env.ref("pcv_sign_ticket.view_sign_ticket_form").id, "form")],
            })
        else:
            action.update({
                "view_mode": "list,form",
                "views": [
                    (self.env.ref("pcv_sign_ticket.view_sign_ticket_list").id, "list"),
                    (self.env.ref("pcv_sign_ticket.view_sign_ticket_form").id, "form")
                ],
            })
        return action
