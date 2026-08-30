from sqlalchemy import create_engine
from sqlalchemy.dialects import registry
from sqlalchemy.dialects.mysql.pymysql import MySQLDialect_pymysql

from app.core.config import settings


class LegacyMySQLDialect(MySQLDialect_pymysql):
    def get_isolation_level(self, dbapi_connection):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SELECT @@tx_isolation")
            value = cursor.fetchone()[0]
            return value.upper().replace("-", " ")
        finally:
            cursor.close()


registry.register(
    "mysql.legacy_pymysql",
    __name__,
    "LegacyMySQLDialect",
)

url = settings.database_url.replace(
    "mysql+pymysql://",
    "mysql+legacy_pymysql://",
    1,
)

engine = create_engine(url, pool_pre_ping=True)

print("Engine created successfully")

with engine.connect() as connection:
    print("CONNECTED SUCCESSFULLY")
    print("Isolation level:", connection.get_isolation_level())

engine.dispose()

print("Test completed successfully")