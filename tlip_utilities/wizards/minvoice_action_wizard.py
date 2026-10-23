from odoo import models

class MInvoiceActionWizard(models.TransientModel):
    _inherit = 'minvoice.action.wizard'

    def _prepare_minvoice_items_vals(self):
        item_infos = super()._prepare_minvoice_items_vals()
    
        lines = self.move_id.lines_to_publish_minvoice()    
        for (item_info, line) in zip(item_infos, lines):
            item_info.update({
                'chi_so_cu': line.last_value,
                'chi_so_moi': line.new_value,
                'he_so_nhan': line.multiplier,
                'tientieuthu_congsuatmay': line.connection_quantity,
                'ty_le_tinh_phi': line.connection_rate
            })
        
        return item_infos
    
    def _prepare_minvoice_extra_vals(self):
        result = super()._prepare_minvoice_extra_vals()
        move = self.move_id
        if move.electricity_consumption_id:
            result.update({
                'tu_ngay': move.electricity_consumption_id.date_from.strftime('%Y-%m-%d'),
                'den_ngay': move.electricity_consumption_id.date_to.strftime('%Y-%m-%d'),
                'cos_phi': str(move.electricity_consumption_id.cosphi),
                'heso_k': str(move.electricity_consumption_id.kfactor),
                'vi_tri': move.electricity_consumption_id.electricity_point_id.electricity_point_name or move.electricity_consumption_id.electricity_point_id.name
            })
        if move.water_consumption_id:
            result.update({
                'tu_ngay': move.water_consumption_id.date_from.strftime('%Y-%m-%d'),
                'den_ngay': move.water_consumption_id.date_to.strftime('%Y-%m-%d'),
                'vi_tri': move.water_consumption_id.water_point_id.name
            })
        return result