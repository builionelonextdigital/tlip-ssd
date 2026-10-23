from odoo import models, fields, api
from typing import Literal


class ApprovalMatrixMixin(models.AbstractModel):
    _inherit = 'approval.matrix.mixin'

    def _get_approvers_signatures(self, approvers=None, type: Literal['signature', 'initial'] = 'signature'):
        self.ensure_one()
        if approvers is None:
            approvers = self.approver_ids

        if not approvers:
            return []

        signatures = []
        for approver in approvers:
            if approver.status != 'approved':
                signatures.append(None)
                continue

            employee = approver._get_employee()
            if type == 'signature':
                signatures.append(employee.e_signature_file)
            elif type == 'initial':
                signatures.append(employee.initial_signature_file)
            else:
                signatures.append(None)            

        return signatures

    def _get_approvers_initial_signatures(self, approvers=None):
        self.ensure_one()
        if approvers is None:
            approvers = self.approver_ids

        if not approvers:
            return []

        return [
            approver._get_employee().initial_signature_file \
                if approver.review_status == 'approved' else None
            for approver in approvers
        ]
