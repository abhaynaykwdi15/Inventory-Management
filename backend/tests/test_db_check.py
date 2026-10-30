from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

from mysql.connector import Error as MySQLDatabaseError

from app import db_check


def test_main_reports_success_without_printing_password(monkeypatch, capsys):
    settings = SimpleNamespace(
        mysql_user="inventory_app",
        mysql_host="127.0.0.1",
        mysql_port=3306,
        mysql_database="inventory_management",
        mysql_password="must-not-be-printed",
    )
    cursor = MagicMock()
    cursor.fetchone.return_value = (1,)
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    pool = Mock()
    pool.get_connection.return_value = connection
    monkeypatch.setattr(db_check, "Settings", Mock(return_value=settings))
    monkeypatch.setattr(db_check, "create_pool", Mock(return_value=pool))

    assert db_check.main() == 0

    output = capsys.readouterr()
    assert "Connection succeeded" in output.out
    assert settings.mysql_password not in output.out + output.err
    cursor.execute.assert_called_once_with("SELECT 1")
    connection.close.assert_called_once()


def test_main_reports_mysql_error_without_exposing_exception(monkeypatch, capsys):
    settings = SimpleNamespace(
        mysql_user="inventory_app",
        mysql_host="127.0.0.1",
        mysql_port=3306,
        mysql_database="inventory_management",
        mysql_password="must-not-be-printed",
    )
    monkeypatch.setattr(db_check, "Settings", Mock(return_value=settings))
    monkeypatch.setattr(
        db_check,
        "create_pool",
        Mock(side_effect=MySQLDatabaseError(msg="access denied; secret value", errno=1045)),
    )

    assert db_check.main() == 1

    output = capsys.readouterr()
    assert "MySQL error 1045" in output.err
    assert "secret value" not in output.out + output.err
    assert settings.mysql_password not in output.out + output.err
