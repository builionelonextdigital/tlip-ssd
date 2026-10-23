from odoo import api, fields, models



class PaymentReport(models.Model):
    _name = "payment.report"
    _description = "Sales Analysis Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'
    
    
    date = fields.Date(string="Value Date")
    bank_id = fields.Many2one('res.bank', string='Bank')
    payment_type = fields.Selection([('direct_debit', 'Direct Debit'),
                                     ('remittance', 'Remittance')], string='Type')
    amount = fields.Float(string='Amount')
    beneficiary_name = fields.Char(string="Beneficiary's name")
    description = fields.Char(string="Description")
    remark = fields.Char(string="Remark")
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency')

    def _select_payment(self):
        select_ = f"""
            MIN(payment.id) AS id,
            payment.currency_id AS currency_id,
            payment.memo AS description,
            payment.date AS date,
            rpb.bank_id AS bank_id,
            brp.name AS beneficiary_name,
            SUM(payment.amount) AS amount,
            CASE
                WHEN rp.direct_debit THEN 'direct_debit'
            ELSE
                'remittance' END AS payment_type,
            '' AS remark
           """
            
        return select_
    
    def _from_payment(self):
        
            # JOIN {currency_table} ON account_currency_table.company_id = s.company_id
        currency_table = self.env['res.currency']._get_simple_currency_table(self.env.companies)
        currency_table = self.env.cr.mogrify(currency_table).decode(self.env.cr.connection.encoding)
        return f"""
            account_payment payment
            LEFT JOIN res_partner rp ON rp.id=payment.partner_id
            LEFT JOIN res_partner_bank rpb ON rpb.id=payment.partner_bank_id
            LEFT JOIN res_partner brp ON brp.id=rpb.partner_id
            """

    def _where_payment(self):
        return """
            payment.payment_type = 'outbound'"""

    def _group_by_payment(self):
        return """
                rp.direct_debit,
                rpb.bank_id,
                brp.name,
                payment.date,
                payment.memo,
                payment.currency_id
            """
    
    def _query(self):
        return f"""
            SELECT {self._select_payment()}
            FROM {self._from_payment()}
            WHERE {self._where_payment()}
            GROUP BY {self._group_by_payment()}
        """
    
    @property
    def _table_query(self):
        return self._query()