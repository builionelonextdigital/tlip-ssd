from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_migration_journal = fields.Boolean(
        help="Indicates if this is a migration journal"
    )
