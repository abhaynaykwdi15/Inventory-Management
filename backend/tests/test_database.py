from unittest.mock import MagicMock, Mock

from app.database import ensure_auth_schema


def test_ensure_auth_schema_creates_only_missing_account_tables():
    cursor = MagicMock()
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    pool = Mock()
    pool.get_connection.return_value = connection

    ensure_auth_schema(pool)

    statements = [call.args[0] for call in cursor.execute.call_args_list]
    assert len(statements) == 3
    assert "CREATE TABLE IF NOT EXISTS app_users" in statements[0]
    assert "CREATE TABLE IF NOT EXISTS user_sessions" in statements[1]
    assert "CREATE TABLE IF NOT EXISTS account_tokens" in statements[2]
    assert all("DROP TABLE" not in statement for statement in statements)
    connection.close.assert_called_once_with()
