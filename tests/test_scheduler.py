"""Tests for alarm_clock.scheduler"""

import pytest
from datetime import datetime
from alarm_clock.alarm import Alarm
from alarm_clock.scheduler import AlarmScheduler, SchedulerError
from alarm_clock.storage import Storage


@pytest.fixture
def scheduler(tmp_path):
    storage = Storage(path=tmp_path / "alarms.json")
    return AlarmScheduler(storage=storage)


class TestAdd:
    def test_add_returns_alarm(self, scheduler):
        alarm = scheduler.add("07:30")
        assert alarm.hour == 7
        assert alarm.minute == 30
        assert alarm.active is True

    def test_add_with_label(self, scheduler):
        alarm = scheduler.add("08:00", label="standup")
        assert alarm.label == "standup"

    def test_add_persists(self, scheduler):
        scheduler.add("07:30")
        alarms = scheduler.list_alarms()
        assert len(alarms) == 1

    def test_add_invalid_time_raises(self, scheduler):
        with pytest.raises(ValueError):
            scheduler.add("99:99")

    def test_add_duplicate_active_raises(self, scheduler):
        scheduler.add("07:30")
        with pytest.raises(SchedulerError, match="already exists"):
            scheduler.add("07:30")

    def test_add_duplicate_after_cancel_succeeds(self, scheduler):
        a = scheduler.add("07:30")
        scheduler.cancel(a.id)
        # Should not raise — the original is inactive
        new = scheduler.add("07:30")
        assert new.active is True

    def test_multiple_different_times(self, scheduler):
        scheduler.add("07:00")
        scheduler.add("08:00")
        scheduler.add("09:00")
        assert len(scheduler.list_alarms()) == 3


class TestCancel:
    def test_cancel_deactivates(self, scheduler):
        alarm = scheduler.add("07:30")
        cancelled = scheduler.cancel(alarm.id)
        assert cancelled.active is False

    def test_cancel_persists(self, scheduler):
        alarm = scheduler.add("07:30")
        scheduler.cancel(alarm.id)
        alarms = scheduler.list_alarms(include_inactive=True)
        assert alarms[0].active is False

    def test_cancel_not_in_active_list(self, scheduler):
        alarm = scheduler.add("07:30")
        scheduler.cancel(alarm.id)
        assert len(scheduler.list_alarms()) == 0

    def test_cancel_nonexistent_raises(self, scheduler):
        with pytest.raises(SchedulerError, match="No alarm found"):
            scheduler.cancel("notanid")

    def test_cancel_already_inactive_raises(self, scheduler):
        alarm = scheduler.add("07:30")
        scheduler.cancel(alarm.id)
        with pytest.raises(SchedulerError, match="already inactive"):
            scheduler.cancel(alarm.id)

    def test_cancel_by_prefix(self, scheduler):
        alarm = scheduler.add("07:30")
        prefix = alarm.id[:4]
        cancelled = scheduler.cancel(prefix)
        assert cancelled.id == alarm.id

    def test_cancel_ambiguous_prefix_raises(self, scheduler):
        a1 = scheduler.add("07:30")
        a2 = scheduler.add("08:00")
        # Force a shared prefix by patching IDs in storage
        storage = scheduler.storage
        alarms = storage.load()
        alarms[0].id = "aaaa1111"
        alarms[1].id = "aaaa2222"
        storage.save(alarms)
        with pytest.raises(SchedulerError, match="Ambiguous"):
            scheduler.cancel("aaaa")


class TestListAlarms:
    def test_empty(self, scheduler):
        assert scheduler.list_alarms() == []

    def test_lists_active_only_by_default(self, scheduler):
        a = scheduler.add("07:30")
        scheduler.cancel(a.id)
        scheduler.add("08:00")
        assert len(scheduler.list_alarms()) == 1

    def test_include_inactive(self, scheduler):
        a = scheduler.add("07:30")
        scheduler.cancel(a.id)
        all_alarms = scheduler.list_alarms(include_inactive=True)
        assert len(all_alarms) == 1
        assert all_alarms[0].active is False

    def test_sorted_by_time(self, scheduler):
        scheduler.add("12:00")
        scheduler.add("07:00")
        scheduler.add("09:30")
        times = [(a.hour, a.minute) for a in scheduler.list_alarms()]
        assert times == sorted(times)


class TestGetDue:
    def test_returns_matching_alarm(self, scheduler):
        scheduler.add("07:30")
        dt = datetime(2024, 1, 1, 7, 30, 0)
        due = scheduler.get_due(dt)
        assert len(due) == 1

    def test_no_match(self, scheduler):
        scheduler.add("07:30")
        dt = datetime(2024, 1, 1, 8, 0, 0)
        assert scheduler.get_due(dt) == []

    def test_inactive_not_returned(self, scheduler):
        a = scheduler.add("07:30")
        scheduler.cancel(a.id)
        dt = datetime(2024, 1, 1, 7, 30, 0)
        assert scheduler.get_due(dt) == []

    def test_multiple_same_minute(self, scheduler):
        """Two alarms at the same time (edge case — both are returned)."""
        storage = scheduler.storage
        from alarm_clock.alarm import Alarm as A
        storage.save([
            A(hour=7, minute=30, id="aaaa1111"),
            A(hour=7, minute=30, id="bbbb2222"),
        ])
        dt = datetime(2024, 1, 1, 7, 30, 0)
        due = scheduler.get_due(dt)
        assert len(due) == 2


class TestMarkFired:
    def test_marks_alarm_inactive(self, scheduler):
        alarm = scheduler.add("07:30")
        scheduler.mark_fired([alarm.id])
        alarms = scheduler.list_alarms(include_inactive=True)
        assert alarms[0].active is False

    def test_only_marks_specified_ids(self, scheduler):
        a1 = scheduler.add("07:30")
        a2 = scheduler.add("08:00")
        scheduler.mark_fired([a1.id])
        active = scheduler.list_alarms()
        assert len(active) == 1
        assert active[0].id == a2.id

    def test_unknown_id_is_a_noop(self, scheduler):
        scheduler.add("07:30")
        scheduler.mark_fired(["notanid"])
        assert len(scheduler.list_alarms()) == 1
