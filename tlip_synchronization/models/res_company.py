import pyodbc
import mysql.connector
import logging
import time
from mysql.connector import Error as MySQLError
from odoo import models, fields

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    power_driver = fields.Char(default="{ODBC Driver 18 for SQL Server}")
    power_server = fields.Char(groups='base.group_system')
    power_database = fields.Char(groups='base.group_system')
    power_username = fields.Char(groups='base.group_system')
    power_password = fields.Char(groups='base.group_system')

    water_server = fields.Char(groups='base.group_system')
    water_database = fields.Char(groups='base.group_system')
    water_username = fields.Char(groups='base.group_system')
    water_password = fields.Char(groups='base.group_system')

    hrms_driver = fields.Char(default="{ODBC Driver 18 for SQL Server}")
    hrms_server = fields.Char(groups='base.group_system')
    hrms_database = fields.Char(groups='base.group_system')
    hrms_username = fields.Char(groups='base.group_system')
    hrms_password = fields.Char(groups='base.group_system')
    hrms_journal_id = fields.Many2one(
        'account.journal', string='HRMS Journal')
    hrms_company_id = fields.Integer()
    item_utility_mapping_ids = fields.One2many('item.utility.mapping', 'company_id')

    def _get_credential_data(self, data_type):
        self = self.sudo()
        data = {
            'server': getattr(self, f'{data_type}_server'),
            'username': getattr(self, f'{data_type}_username'),
            'password': getattr(self, f'{data_type}_password'),
            'database': getattr(self, f'{data_type}_database'),
        }
        if data_type in ['power', 'hrms']:
            data.update({
                'driver': getattr(self, f'{data_type}_driver')
            })
        return data

    def _execute_mssql_query(self, credential_data, sql_query):
        try:
            # Connect to the SQL Server
            conn = self._retry_connect_mssql(credential_data)
            cursor = conn.cursor()

            # Execute the query
            cursor.execute(sql_query)

            # Fetch and print the results
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results or [], 'Success'
        except Exception as err:
            server = credential_data.get('server')
            message = f"Execute query on MSSQL {server} failed! Error: {str(err)}"
            _logger.error(message)
            return [], message
        finally:
            # Close the connection
            if 'conn' in locals() and conn:
                conn.close()

    def _execute_mysql_query(self, credential_data, sql_query):
        try:
            # Connect to the MySQL database
            connection = self._retry_connect_mysql(credential_data)

            # Create a cursor object
            cursor = connection.cursor(dictionary=True)

            # Execute the query
            cursor.execute(sql_query)

            # Fetch the results
            rows = cursor.fetchall()
            return rows or []

        except MySQLError as err:
            server = credential_data.get('server')
            _logger.error(
                f"Execute query on MySQL {server} failed! Error: {str(err)}")
            return []
        finally:
            # Close the database connection
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def get_product_by_code(self, utility_type, code):
        self.ensure_one()
        lines = self.item_utility_mapping_ids.filtered(lambda l: l.utility_type == utility_type and l.item_code == code)
        if lines:
            return lines[0].product_id
        return self.env['product.product'].browse()

    def _retry_connect_mssql(self, credential_data, delay=1, attempts=3):
        driver = credential_data.get('driver')
        server = credential_data.get('server')
        database = credential_data.get('database')
        username = credential_data.get('username')
        password = credential_data.get('password')
        for attempt in range(attempts):
            try:
                conn = pyodbc.connect(
                    f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes', timeout=120
                )
                return conn
            except Exception as err:
                if attempt == attempts - 1:
                    raise err
                time.sleep(delay)

    def _retry_connect_mysql(self, credential_data, delay=1, attempts=3):
        server = credential_data.get('server')
        database = credential_data.get('database')
        username = credential_data.get('username')
        password = credential_data.get('password')
        for attempt in range(attempts):
            try:
                connection = mysql.connector.connect(
                    host=server,
                    user=username,
                    password=password,
                    database=database,
                    connection_timeout=120
                    # Localhost need this param to run
                    # ssl_disabled='True'
                )
                if connection.is_connected():
                    return connection
                else:
                    raise MySQLError("Connection failed")
            except Exception as err:
                if attempt == attempts - 1:
                    raise err
                time.sleep(delay)
