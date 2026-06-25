# alarm_clock

A simple, dependency-free CLI alarm clock written in Python.

## Features

- Set alarms by time (`HH:MM`, 24-hour format)
- Optional labels per alarm
- List active (or all) alarms
- Cancel an alarm by ID
- Persistent state across restarts (JSON file, atomic writes, file locking)
- Foreground daemon with clean Ctrl+C handling
- Audio alert via OS-native sound; falls back to terminal BEL

---

## Requirements

- Python 3.10+
- No third-party runtime dependencies

---

## Installation

```bash
# Clone or unzip the project
cd alarm_clock

# Install in editable mode (adds the `alarm` command to your PATH)
pip install -e .
```

For development (includes pytest):

```bash
pip install -e ".[dev]"
```

---

## Usage

### Set an alarm

```bash
alarm set 07:30
alarm set 07:30 -l "morning run"
alarm set 23:00 --label "night meds"
```

Times are always 24-hour format. Setting a time that has already passed today
schedules it for the next occurrence when the daemon checks.

### List alarms

```bash
alarm list           # active alarms only (default)
alarm list --all     # include fired/cancelled alarms
alarm list -a
```

### Cancel an alarm

```bash
alarm cancel <id>    # full ID or unique prefix, e.g. alarm cancel a1b2
```

### Start the daemon

```bash
alarm start
```

The daemon polls every 30 seconds. Leave it running in a terminal tab, or use
`screen` / `tmux` / `nohup` to keep it alive after you close the terminal:

```bash
nohup alarm start &
```

Press **Ctrl+C** to stop the daemon.

---

## State file

Alarms are stored in:

```
~/.config/alarm_clock/alarms.json
```

Override the path with the environment variable:

```bash
export ALARM_STATE_FILE=/tmp/my_alarms.json
alarm set 08:00
```

This is also how tests isolate themselves from your real alarm file.

---

## Architecture

```
alarm_clock/
├── alarm_clock/
│   ├── alarm.py       # Alarm dataclass, parsing, serialization
│   ├── storage.py     # JSON persistence with file locking
│   ├── scheduler.py   # add / cancel / list / get_due / mark_fired
│   ├── notifier.py    # OS audio + terminal BEL fallback
│   ├── daemon.py      # 30 s polling loop
│   └── cli.py         # argparse entry point
└── tests/
    ├── test_alarm.py
    ├── test_storage.py
    ├── test_scheduler.py
    └── test_cli.py
```

Each layer only depends on layers below it. `cli.py` is intentionally thin —
all business logic lives in `scheduler.py`.

---

## Running tests

```bash
pytest                        # all tests
pytest -v                     # verbose
pytest --cov=alarm_clock      # with coverage (requires pytest-cov)
pytest tests/test_alarm.py    # single module
```

Tests never touch your real `~/.config/alarm_clock/alarms.json` — each test
gets an isolated `tmp_path` directory via pytest fixtures.

---

## Edge cases handled

| Scenario | Behaviour |
|---|---|
| Duplicate alarm time | Error: cancel the existing one first |
| Alarm time already passed | Sets for that time; fires next time daemon polls it |
| Missing state file | Treated as empty — no error |
| Corrupt state file | `StorageError` with a clear message |
| Two processes writing simultaneously | Advisory file lock prevents corruption |
| SIGINT while alarm is ringing | Cleans up and exits; prints `[alarm dismissed]` |
| No audio device | Falls back to terminal BEL (`\a`) |
| Computer asleep during alarm | Alarm is missed — a known limitation of polling |

---

## Notes

- **Recurring alarms** (daily, weekday) are not in MVP scope.
- **Snooze** is not implemented.
- The daemon must be running for alarms to fire. It does **not** auto-start
  on login — use your OS's startup mechanism for that (launchd, systemd user
  units, Task Scheduler).

---

## License

MIT
