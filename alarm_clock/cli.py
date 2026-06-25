"""CLI entry point: alarm set | list | cancel | start"""

import argparse
import sys

from alarm_clock.scheduler import AlarmScheduler, SchedulerError
from alarm_clock.storage import StorageError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alarm",
        description="A simple CLI alarm clock.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # --- set ---
    p_set = sub.add_parser("set", help="Set a new alarm (HH:MM, 24-hour).")
    p_set.add_argument("time", help="Time in HH:MM format, e.g. 07:30")
    p_set.add_argument(
        "-l", "--label", default="", help="Optional label for the alarm."
    )

    # --- list ---
    p_list = sub.add_parser("list", help="List active alarms.")
    p_list.add_argument(
        "-a", "--all", action="store_true", help="Include inactive (fired) alarms."
    )

    # --- cancel ---
    p_cancel = sub.add_parser("cancel", help="Cancel an alarm by ID.")
    p_cancel.add_argument("id", help="Alarm ID (or unique prefix) to cancel.")

    # --- start ---
    sub.add_parser("start", help="Start the alarm daemon (foreground).")

    return parser


def cmd_set(args, scheduler: AlarmScheduler) -> int:
    try:
        alarm = scheduler.add(args.time, label=args.label)
        print(f"Alarm set: {alarm}")
        return 0
    except (ValueError, SchedulerError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_list(args, scheduler: AlarmScheduler) -> int:
    alarms = scheduler.list_alarms(include_inactive=args.all)
    if not alarms:
        label = "alarms" if args.all else "active alarms"
        print(f"No {label}.")
        return 0
    for alarm in alarms:
        print(alarm)
    return 0


def cmd_cancel(args, scheduler: AlarmScheduler) -> int:
    try:
        alarm = scheduler.cancel(args.id)
        print(f"Cancelled: {alarm}")
        return 0
    except SchedulerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_start(args, scheduler: AlarmScheduler) -> int:  # noqa: ARG001
    from alarm_clock.daemon import run
    run(scheduler)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    scheduler = AlarmScheduler()

    try:
        dispatch = {
            "set": cmd_set,
            "list": cmd_list,
            "cancel": cmd_cancel,
            "start": cmd_start,
        }
        return dispatch[args.command](args, scheduler)
    except StorageError as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 2


def entry_point():
    sys.exit(main())


if __name__ == "__main__":
    entry_point()
