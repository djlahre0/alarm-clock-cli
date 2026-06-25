"""Tests for alarm_clock.alarm"""

import pytest
from datetime import datetime
from alarm_clock.alarm import Alarm


class TestAlarmConstruction:
    def test_valid_alarm(self):
        a = Alarm(hour=7, minute=30)
        assert a.hour == 7
        assert a.minute == 30
        assert a.active is True
        assert a.label == ""
        assert len(a.id) == 8

    def test_id_is_unique(self):
        ids = {Alarm(7, 30).id for _ in range(50)}
        assert len(ids) == 50

    def test_invalid_hour_low(self):
        with pytest.raises(ValueError, match="hour"):
            Alarm(hour=-1, minute=0)

    def test_invalid_hour_high(self):
        with pytest.raises(ValueError, match="hour"):
            Alarm(hour=24, minute=0)

    def test_invalid_minute_low(self):
        with pytest.raises(ValueError, match="minute"):
            Alarm(hour=0, minute=-1)

    def test_invalid_minute_high(self):
        with pytest.raises(ValueError, match="minute"):
            Alarm(hour=0, minute=60)

    def test_midnight(self):
        a = Alarm(hour=0, minute=0)
        assert a.hour == 0
        assert a.minute == 0

    def test_end_of_day(self):
        a = Alarm(hour=23, minute=59)
        assert a.hour == 23
        assert a.minute == 59


class TestFromTimeString:
    def test_zero_padded(self):
        a = Alarm.from_time_string("07:30")
        assert a.hour == 7
        assert a.minute == 30

    def test_no_padding(self):
        a = Alarm.from_time_string("7:30")
        assert a.hour == 7

    def test_midnight(self):
        a = Alarm.from_time_string("00:00")
        assert a.hour == 0
        assert a.minute == 0

    def test_with_label(self):
        a = Alarm.from_time_string("08:00", label="standup")
        assert a.label == "standup"

    def test_invalid_format_no_colon(self):
        with pytest.raises(ValueError, match="Invalid time format"):
            Alarm.from_time_string("0730")

    def test_invalid_format_letters(self):
        with pytest.raises(ValueError, match="Invalid time format"):
            Alarm.from_time_string("banana")

    def test_invalid_hour_out_of_range(self):
        with pytest.raises(ValueError):
            Alarm.from_time_string("25:00")

    def test_invalid_minute_out_of_range(self):
        with pytest.raises(ValueError):
            Alarm.from_time_string("07:99")

    def test_extra_whitespace(self):
        a = Alarm.from_time_string("  09:15  ")
        assert a.hour == 9
        assert a.minute == 15

    def test_three_parts_raises(self):
        with pytest.raises(ValueError, match="Invalid time format"):
            Alarm.from_time_string("07:30:00")


class TestMatchesNow:
    def test_matches_exact_time(self):
        a = Alarm(hour=7, minute=30)
        dt = datetime(2024, 1, 1, 7, 30, 45)
        assert a.matches_now(dt) is True

    def test_does_not_match_wrong_hour(self):
        a = Alarm(hour=7, minute=30)
        dt = datetime(2024, 1, 1, 8, 30, 0)
        assert a.matches_now(dt) is False

    def test_does_not_match_wrong_minute(self):
        a = Alarm(hour=7, minute=30)
        dt = datetime(2024, 1, 1, 7, 31, 0)
        assert a.matches_now(dt) is False

    def test_inactive_alarm_never_matches(self):
        a = Alarm(hour=7, minute=30, active=False)
        dt = datetime(2024, 1, 1, 7, 30, 0)
        assert a.matches_now(dt) is False

    def test_matches_regardless_of_seconds(self):
        a = Alarm(hour=12, minute=0)
        for sec in [0, 15, 30, 59]:
            dt = datetime(2024, 6, 1, 12, 0, sec)
            assert a.matches_now(dt) is True


class TestSerialization:
    def test_round_trip(self):
        original = Alarm(hour=9, minute=5, label="coffee", id="abc12345")
        restored = Alarm.from_dict(original.to_dict())
        assert restored.hour == original.hour
        assert restored.minute == original.minute
        assert restored.label == original.label
        assert restored.id == original.id
        assert restored.active == original.active
        assert restored.created_at == original.created_at

    def test_to_dict_keys(self):
        a = Alarm(7, 30)
        d = a.to_dict()
        assert set(d.keys()) == {"id", "hour", "minute", "label", "active", "created_at"}

    def test_from_dict_missing_optional_fields(self):
        data = {"id": "aaaabbbb", "hour": 6, "minute": 0}
        a = Alarm.from_dict(data)
        assert a.label == ""
        assert a.active is True

    def test_inactive_round_trip(self):
        a = Alarm(7, 30, active=False)
        restored = Alarm.from_dict(a.to_dict())
        assert restored.active is False


class TestStr:
    def test_str_active_no_label(self):
        a = Alarm(hour=7, minute=5, id="abc12345")
        assert str(a) == "[abc12345] 07:05 (on)"

    def test_str_with_label(self):
        a = Alarm(hour=8, minute=0, id="abc12345", label="gym")
        assert "gym" in str(a)
        assert "08:00" in str(a)

    def test_str_inactive(self):
        a = Alarm(hour=7, minute=0, id="abc12345", active=False)
        assert "(off)" in str(a)
