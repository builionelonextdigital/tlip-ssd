from odoo import api, Command, models
from odoo.tools import format_date, format_datetime


class CRMixin(models.AbstractModel):
    _name = "cr.mixin"
    _description = "Change Request Mixin"

    @api.model
    def check_records_have_change(self, current_many_vals, new_many_vals):
        if len(current_many_vals) != len(new_many_vals):
            return True

        fields_to_compare = [
            name for name, field in current_many_vals._fields.items()
            if field.store and field.copy and not field.automatic
        ]

        for current, new in zip(current_many_vals, new_many_vals):
            if any(current[field] != new[field] for field in fields_to_compare if hasattr(current, field) and hasattr(new, field)):
                return True

        return False

    @api.model
    def convert_value_to_updated_val(self, field, value):
        field_type = field.type
        if field_type == 'many2one':
            new_value = value.id
        elif field_type == 'many2many':
            new_value = [(6, 0, value.ids)]
        else:
            new_value = value

        return new_value

    def _get_difference_record_changes(self, current_record):
        self.ensure_one()
        fields_to_compare = {name: field
                             for name, field in self.env[self._name]._fields.items() if name in self._fields_tracking_change()}
        summary_change_vals = []
        for name, field in fields_to_compare.items():
            current_val = current_record[name]
            new_val = self[name]
            field_name = field.get_description(self.env).get('string')

            if field.type in ('one2many', 'many2many'):
                if self.check_records_have_change(current_val, new_val):
                    summary_change_vals.append(Command.create({
                        'name': field_name,
                        'new_value': f'{field_name} changed'
                    }))
            elif current_val != new_val:
                if field.type == 'date':
                    current_val = format_date(self.env, current_val)
                    new_val = format_date(self.env, new_val)
                elif field.type == 'datetime':
                    current_val = format_datetime(self.env, current_val)
                    new_val = format_datetime(self.env, new_val)
                else:
                    current_val = field.convert_to_export(
                        current_val, current_record)
                    new_val = field.convert_to_export(new_val, self)

                summary_change_vals.append(Command.create({
                    'name': field_name,
                    'current_value': current_val,
                    'new_value': new_val
                }))
        return summary_change_vals

    def _fields_tracking_change(self):
        return []
