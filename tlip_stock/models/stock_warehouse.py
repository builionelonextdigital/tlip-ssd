from odoo import api, fields, models, _


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    dispose_type_id = fields.Many2one('stock.picking.type', 'Dispose Type', check_company=True)
    damage_type_id = fields.Many2one('stock.picking.type', 'Damage Type', check_company=True)
    maintenance_type_id = fields.Many2one('stock.picking.type', 'Maintenance Type', check_company=True)
    inspect_type_id = fields.Many2one('stock.picking.type', 'Inspect Type', check_company=True)

    def _get_sequence_values(self, name=False, code=False):
        values = super(StockWarehouse, self)._get_sequence_values(name=name, code=code)
        values.update({
            'dispose_type_id': {'name': _('%(name)s Sequence Dispose', name=self.name), 'prefix': self.code + '/' + (self.dispose_type_id.sequence_code or 'DISPOSE') + '/', 'padding': 5, 'company_id': self.company_id.id},
            'damage_type_id': {'name': _('%(name)s Sequence Damage', name=self.name), 'prefix': self.code + '/' + (self.dispose_type_id.sequence_code or 'DAMAGE') + '/', 'padding': 5, 'company_id': self.company_id.id},
            'maintenance_type_id': {'name': _('%(name)s Sequence Maintenance', name=self.name), 'prefix': self.code + '/' + (self.dispose_type_id.sequence_code or 'MAINTENANCE') + '/', 'padding': 5, 'company_id': self.company_id.id},
            'inspect_type_id': {'name': _('%(name)s Sequence Inspect', name=self.name), 'prefix': self.code + '/' + (self.inspect_type_id.sequence_code or 'INSPECT') + '/', 'padding': 5, 'company_id': self.company_id.id},
        })
        return values

    def _get_picking_type_create_values(self, max_sequence):
        data, next_sequence = super(StockWarehouse, self)._get_picking_type_create_values(max_sequence)
        data.update({
            'dispose_type_id': {
                'name': _('Dispose'),
                'code': 'internal',
                'internal_code': 'dispose',
                'use_create_lots': True,
                'use_existing_lots': True,
                'sequence': next_sequence + 1,
                'sequence_code': 'DISPOSE',
                'company_id': self.company_id.id,
                'create_backorder': 'never'
            },
            'damage_type_id': {
                'name': _('Damage'),
                'code': 'internal',
                'internal_code': 'damage',
                'use_create_lots': True,
                'use_existing_lots': True,
                'sequence': next_sequence + 1,
                'sequence_code': 'DAMAGE',
                'company_id': self.company_id.id,
                'create_backorder': 'never'
            },
            'maintenance_type_id': {
                'name': _('Maintenance'),
                'code': 'internal',
                'internal_code': 'maintenance',
                'use_create_lots': True,
                'use_existing_lots': True,
                'sequence': next_sequence + 1,
                'sequence_code': 'MAINTENANCE',
                'company_id': self.company_id.id,
                'create_backorder': 'never'
            },
            'inspect_type_id': {
                'name': _('Inspect'),
                'code': 'internal',
                'internal_code': 'inspect',
                'use_create_lots': True,
                'use_existing_lots': True,
                'sequence': next_sequence + 1,
                'sequence_code': 'INSPECT',
                'company_id': self.company_id.id,
                'create_backorder': 'never'
            },
        })
        return data, max_sequence + 1

    def _get_picking_type_update_values(self):
        data = super(StockWarehouse, self)._get_picking_type_update_values()
        data.update({
            'dispose_type_id': {
                'barcode': self.code.replace(" ", "").upper() + "DISPOSE",
            },
            'damage_type_id': {
                'barcode': self.code.replace(" ", "").upper() + "DAMAGE",
            },
            'maintenance_type_id': {
                'barcode': self.code.replace(" ", "").upper() + "MAINTENANCE",
            },
            'inspect_type_id': {
                'barcode': self.code.replace(" ", "").upper() + "INSPECT",
            },
        })
        return data

    @api.model
    def _create_missing_operation_type_warehouse(self):
        for warehouse in self.search(['|', '|', '|', ('dispose_type_id', '=', False), ('damage_type_id', '=', False), ('maintenance_type_id', '=', False), ('inspect_type_id', '=', False)]):
            picking_type_vals = warehouse._create_or_update_sequences_and_picking_types()
            if picking_type_vals:
                warehouse.write(picking_type_vals)
