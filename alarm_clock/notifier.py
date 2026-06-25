"""Fire an alert: terminal bell + optional audio playback."""

import sys
import time as _time
import threading

from alarm_clock.alarm import Alarm

_ringing = threading.Event()


def _beep_loop(alarm: Alarm, duration_seconds: int = 60) -> None:
    """Write BEL characters to the terminal for up to `duration_seconds`."""
    end = _time.monotonic() + duration_seconds
    while _time.monotonic() < end and not _ringing.is_set():
        sys.stdout.write("\a")
        sys.stdout.flush()
        _time.sleep(1)


def _try_play_audio(alarm: Alarm) -> bool:
    """Try playsound → winsound → aplay → afplay. Return True on success."""
    try:
        import playsound  # optional dependency
        playsound.playsound(None)  # will fail — just checking import
    except Exception:
        pass

    # macOS
    if sys.platform == "darwin":
        try:
            import subprocess
            subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"])
            return True
        except FileNotFoundError:
            pass

    # Windows
    if sys.platform == "win32":
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            return True
        except Exception:
            pass

    # Linux (aplay)
    if sys.platform.startswith("linux"):
        try:
            import subprocess
            subprocess.Popen(["aplay", "/usr/share/sounds/alsa/Front_Center.wav"])
            return True
        except FileNotFoundError:
            pass

    return False


def ring(alarm: Alarm, duration_seconds: int = 60) -> None:
    """
    Alert the user that `alarm` has fired.

    Prints a visual banner, attempts OS audio, and falls back to terminal BEL.
    Respects SIGINT — pressing Ctrl+C silences the alert cleanly.
    """
    _ringing.clear()

    label_part = f" — {alarm.label}" if alarm.label else ""
    banner = (
        f"\n{'=' * 50}\n"
        f"  ALARM  {alarm.hour:02d}:{alarm.minute:02d}{label_part}\n"
        f"  Press Ctrl+C to dismiss.\n"
        f"{'=' * 50}\n"
    )
    print(banner, flush=True)

    audio_ok = _try_play_audio(alarm)
    if not audio_ok:
        # Fall back to terminal BEL in a thread so the main thread stays interruptible
        t = threading.Thread(
            target=_beep_loop, args=(alarm, duration_seconds), daemon=True
        )
        t.start()

    try:
        _time.sleep(duration_seconds)
    except KeyboardInterrupt:
        _ringing.set()
        print("\n[alarm dismissed]", flush=True)
