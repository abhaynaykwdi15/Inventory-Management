import sys

from mysql.connector import Error as MySQLDatabaseError
from pydantic import ValidationError

from app.config import Settings
from app.database import create_pool


def main() -> int:
    try:
        settings = Settings()
    except ValidationError:
        print(
            "Database configuration is invalid. Check the required INVENTORY_MYSQL_* "
            "settings in backend/.env.",
            file=sys.stderr,
        )
        return 2

    print(
        "Testing MySQL connection to "
        f"{settings.mysql_user}@{settings.mysql_host}:{settings.mysql_port}/"
        f"{settings.mysql_database}"
    )
    connection = None
    try:
        connection = create_pool(settings).get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        if result != (1,):
            print("Connection failed: SELECT 1 returned an unexpected result.", file=sys.stderr)
            return 1
    except MySQLDatabaseError as error:
        print(
            f"Connection failed (MySQL error {error.errno}). "
            "Check the configured account, password, and allowed host.",
            file=sys.stderr,
        )
        return 1
    finally:
        if connection is not None:
            connection.close()

    print("Connection succeeded: SELECT 1 returned 1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
