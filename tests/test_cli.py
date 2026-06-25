"""Tests for alarm_clock.cli (uses CliRunner pattern via subprocess-free approach)."""

import sys
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock
from alarm_clock.cli import main, build_parser
from alarm_clock.scheduler import AlarmScheduler
from alarm_clock.storage import Storage


@pytest.fixture
def scheduler(tmp_path):
    storage = Storage(path=tmp_path / "alarms.json")
    return AlarmScheduler(storage=storage)


def run_cli(argv, scheduler):
    """Run main() with a controlled scheduler injected via mock."""
    with patch("alarm_clock.cli.AlarmScheduler", return_value=scheduler):
        return main(argv)


class TestSetCommand:
    def test_set_valid_time(self, scheduler, capsys):
        rc = run_cli(["set", "07:30"], scheduler)
        assert rc == 0
        out = capsys.readouterr().out
        assert "07:30" in out

    def test_set_with_label(self, scheduler, capsys):
        rc = run_cli(["set", "07:30", "-l", "wake up"], scheduler)
        assert rc == 0
        out = capsys.readouterr().out
        assert "wake up" in out

    def test_set_invalid_time_returns_1(self, scheduler, capsys):
        rc = run_cli(["set", "99:00"], scheduler)
        assert rc == 1
        err = capsys.readouterr().err
        assert err  # some error message

    def test_set_duplicate_returns_1(self, scheduler, capsys):
        run_cli(["set", "07:30"], scheduler)
        rc = run_cli(["set", "07:30"], scheduler)
        assert rc == 1

    def test_set_persists_to_storage(self, scheduler):
        run_cli(["set", "08:00"], scheduler)
        alarms = scheduler.list_alarms()
        assert len(alarms) == 1
        assert alarms[0].hour == 8


class TestListCommand:
    def test_list_empty(self, scheduler, capsys):
        rc = run_cli(["list"], scheduler)
        assert rc == 0
        out = capsys.readouterr().out
        assert "No" in out

    def test_list_shows_alarms(self, scheduler, capsys):
        run_cli(["set", "07:30", "-l", "morning"], scheduler)
        run_cli(["list"], scheduler)
        out = capsys.readouterr().out
        assert "07:30" in out
        assert "morning" in out

    def test_list_all_flag_shows_inactive(self, scheduler, capsys):
        alarm = scheduler.add("07:30")
        scheduler.cancel(alarm.id)
        run_cli(["list", "--all"], scheduler)
        out = capsys.readouterr().out
        assert "off" in out

    def test_list_hides_inactive_by_default(self, scheduler, capsys):
        alarm = scheduler.add("07:30")
        scheduler.cancel(alarm.id)
        rc = run_cli(["list"], scheduler)
        assert rc == 0
        out = capsys.readouterr().out
        assert "No" in out


class TestCancelCommand:
    def test_cancel_valid_id(self, scheduler, capsys):
        alarm = scheduler.add("07:30")
        rc = run_cli(["cancel", alarm.id], scheduler)
        assert rc == 0
        out = capsys.readouterr().out
        assert "Cancelled" in out

    def test_cancel_invalid_id_returns_1(self, scheduler, capsys):
        rc = run_cli(["cancel", "notanid"], scheduler)
        assert rc == 1
        err = capsys.readouterr().err
        assert err

    def test_cancel_removes_from_active_list(self, scheduler):
        alarm = scheduler.add("07:30")
        run_cli(["cancel", alarm.id], scheduler)
        assert scheduler.list_alarms() == []


class TestParserEdgeCases:
    def test_no_command_exits(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_unknown_command_exits(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["explode"])

    def test_help_exits_zero(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
