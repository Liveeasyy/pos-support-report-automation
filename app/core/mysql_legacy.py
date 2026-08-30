from sqlalchemy.dialects.mysql.pymysql import MySQLDialect_pymysql


class LegacyMySQLDialect(MySQLDialect_pymysql):
    """
    Compatibility dialect for the legacy MySQL 8.0.0 DMR server.

    This server exposes @@tx_isolation instead of
    @@transaction_isolation.
    """

    def get_isolation_level(self, dbapi_connection):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SELECT @@tx_isolation")
            row = cursor.fetchone()

            if row is None:
                raise RuntimeError(
                    "Could not retrieve transaction isolation level."
                )

            value = row[0]

            if isinstance(value, bytes):
                value = value.decode()

            return value.upper().replace("-", " ")
        finally:
            cursor.close()