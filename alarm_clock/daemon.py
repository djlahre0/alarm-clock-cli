"""Background polling loop — runs in the foreground until SIGINT."""

import signal
import sys
import time
from datetime import datetime

from alarm_clock.scheduler import AlarmScheduler
from alarm_clock.notifier import ring

_POLL_INTERVAL = 30  # seconds


def _handle_sigterm(signum, frame):
    print("\n[daemon] Received SIGTERM, shutting down.", flush=True)
    sys.exit(0)


def run(scheduler: AlarmScheduler | None = None, poll_interval: int = _POLL_INTERVAL) -> None:
    """
    Poll for due alarms every `poll_interval` seconds.

    - Fires and deactivates any alarms that match the current HH:MM.
    - Skips the minute after firing to avoid double-ringing.
    - Exits cleanly on SIGINT (Ctrl+C) or SIGTERM.
    """
    scheduler = scheduler or AlarmScheduler()
    signal.signal(signal.SIGTERM, _handle_sigterm)

    print("[daemon] Alarm clock running. Press Ctrl+C to stop.", flush=True)
    _list_active(scheduler)

    last_fired_minute: int | None = None

    try:
        while True:
            now = datetime.now()
            current_minute = now.hour * 60 + now.minute

            if current_minute != last_fired_minute:
                due = scheduler.get_due(now)
                if due:
                    ids = [a.id for a in due]
                    scheduler.mark_fired(ids)
                    last_fired_minute = current_minute
                    for alarm in due:
                        ring(alarm)

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\n[daemon] Stopped.", flush=True)


def _list_active(scheduler: AlarmScheduler) -> None:
    alarms = scheduler.list_alarms()
    if alarms:
        print("[daemon] Active alarms:")
        for a in alarms:
            print(f"  {a}")
    else:
        print("[daemon] No active alarms. Set one with: alarm set HH:MM")
    print(flush=True)
