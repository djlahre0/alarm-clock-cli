from dataclasses import dataclass, field
from datetime import datetime, time
import uuid


@dataclass
class Alarm:
    hour: int
    minute: int
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    label: str = ""
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if not (0 <= self.hour <= 23):
            raise ValueError(f"Invalid hour: {self.hour}. Must be 0–23.")
        if not (0 <= self.minute <= 59):
            raise ValueError(f"Invalid minute: {self.minute}. Must be 0–59.")

    @property
    def trigger_time(self) -> time:
        return time(self.hour, self.minute)

    def matches_now(self, dt: datetime | None = None) -> bool:
        """Return True if this alarm is active and the current minute matches."""
        now = dt or datetime.now()
        return self.active and now.hour == self.hour and now.minute == self.minute

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "hour": self.hour,
            "minute": self.minute,
            "label": self.label,
            "active": self.active,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Alarm":
        return cls(
            id=data["id"],
            hour=data["hour"],
            minute=data["minute"],
            label=data.get("label", ""),
            active=data.get("active", True),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )

    @classmethod
    def from_time_string(cls, time_str: str, label: str = "") -> "Alarm":
        """Parse '07:30' or '7:30' into an Alarm (24-hour format)."""
        try:
            parts = time_str.strip().split(":")
            if len(parts) != 2:
                raise ValueError
            hour, minute = int(parts[0]), int(parts[1])
        except (ValueError, AttributeError):
            raise ValueError(
                f"Invalid time format '{time_str}'. Expected HH:MM in 24-hour format."
            )
        return cls(hour=hour, minute=minute, label=label)

    def __str__(self) -> str:
        status = "on" if self.active else "off"
        label_part = f" — {self.label}" if self.label else ""
        return f"[{self.id}] {self.hour:02d}:{self.minute:02d}{label_part} ({status})"
