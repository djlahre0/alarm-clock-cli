"""AlarmScheduler: core business logic for managing alarms."""

from datetime import datetime
from pathlib import Path

from alarm_clock.alarm import Alarm
from alarm_clock.storage import Storage


class SchedulerError(Exception):
    pass


class AlarmScheduler:
    def __init__(self, storage: Storage | None = None):
        self.storage = storage or Storage()

    # ------------------------------------------------------------------ CRUD

    def add(self, time_str: str, label: str = "") -> Alarm:
        """Parse time_str, check for duplicates, persist and return the new alarm."""
        alarm = Alarm.from_time_string(time_str, label=label)
        alarms = self.storage.load()

        duplicates = [
            a for a in alarms
            if a.hour == alarm.hour and a.minute == alarm.minute and a.active
        ]
        if duplicates:
            raise SchedulerError(
                f"An active alarm already exists for "
                f"{alarm.hour:02d}:{alarm.minute:02d} (id: {duplicates[0].id}). "
                f"Cancel it first or use a different time."
            )

        alarms.append(alarm)
        self.storage.save(alarms)
        return alarm

    def cancel(self, alarm_id: str) -> Alarm:
        """Deactivate an alarm by ID prefix. Raises if not found."""
        alarms = self.storage.load()
        matches = [a for a in alarms if a.id.startswith(alarm_id)]

        if not matches:
            raise SchedulerError(f"No alarm found with id '{alarm_id}'.")
        if len(matches) > 1:
            raise SchedulerError(
                f"Ambiguous id '{alarm_id}' matches {len(matches)} alarms. "
                f"Provide more characters."
            )

        target = matches[0]
        if not target.active:
            raise SchedulerError(f"Alarm '{alarm_id}' is already inactive.")

        target.active = False
        self.storage.save(alarms)
        return target

    def list_alarms(self, include_inactive: bool = False) -> list[Alarm]:
        """Return alarms sorted by trigger time."""
        alarms = self.storage.load()
        if not include_inactive:
            alarms = [a for a in alarms if a.active]
        return sorted(alarms, key=lambda a: (a.hour, a.minute))

    # ---------------------------------------------------------------- Daemon

    def get_due(self, dt: datetime | None = None) -> list[Alarm]:
        """Return active alarms that match the current minute."""
        now = dt or datetime.now()
        alarms = self.storage.load()
        return [a for a in alarms if a.matches_now(now)]

    def mark_fired(self, alarm_ids: list[str]) -> None:
        """Deactivate alarms that have just fired."""
        alarms = self.storage.load()
        for alarm in alarms:
            if alarm.id in alarm_ids:
                alarm.active = False
        self.storage.save(alarms)
