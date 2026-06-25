"""JSON persistence with advisory file locking."""

import json
import os
import sys
from pathlib import Path
from typing import Any

from alarm_clock.alarm import Alarm

DEFAULT_STATE_PATH = Path.home() / ".config" / "alarm_clock" / "alarms.json"


def _get_state_path(path: Path | None = None) -> Path:
    env_path = os.environ.get("ALARM_STATE_FILE")
    if env_path:
        return Path(env_path)
    return path or DEFAULT_STATE_PATH


class StorageError(Exception):
    pass


class Storage:
    def __init__(self, path: Path | None = None):
        self.path = _get_state_path(path)

    def _lock_path(self) -> Path:
        return self.path.with_suffix(".lock")

    def _acquire_lock(self):
        """Cross-platform advisory lock via a .lock file."""
        lock = self._lock_path()
        lock.parent.mkdir(parents=True, exist_ok=True)
        if sys.platform != "win32":
            import fcntl
            self._lock_fd = open(lock, "w")
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                self._lock_fd.close()
                raise StorageError(
                    "Another alarm_clock process holds the lock. Try again shortly."
                )
        else:
            # Windows: existence-based lock
            if lock.exists():
                raise StorageError(
                    "Another alarm_clock process holds the lock. Try again shortly."
                )
            lock.touch()

    def _release_lock(self):
        if sys.platform != "win32":
            import fcntl
            fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
            self._lock_fd.close()
        else:
            self._lock_path().unlink(missing_ok=True)

    def load(self) -> list[Alarm]:
        """Load all alarms from disk. Returns [] if file missing or empty."""
        if not self.path.exists():
            return []
        try:
            raw = self.path.read_text(encoding="utf-8").strip()
            if not raw:
                return []
            data: list[dict[str, Any]] = json.loads(raw)
            return [Alarm.from_dict(d) for d in data]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise StorageError(f"State file is corrupt ({self.path}): {exc}") from exc

    def save(self, alarms: list[Alarm]) -> None:
        """Atomically write alarms to disk under an advisory lock."""
        self._acquire_lock()
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps([a.to_dict() for a in alarms], indent=2),
                encoding="utf-8",
            )
            tmp.replace(self.path)
        finally:
            self._release_lock()
