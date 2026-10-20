"""Run a command and verify that it fails for the expected reason."""

from __future__ import annotations

import argparse
import subprocess


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contains",
        action="append",
        required=True,
        help="Text that must appear in the combined command output; repeatable.",
    )
    parser.add_argument(
        "--occurs",
        action="append",
        default=[],
        nargs=2,
        metavar=("TEXT", "COUNT"),
        help="Text and exact occurrence count required in the combined output; repeatable.",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("a command is required after --")
    return args


def main() -> int:
    args = parse_args()
    result = subprocess.run(args.command, check=False, capture_output=True, text=True)
    combined_output = result.stdout + result.stderr
    print(combined_output, end="" if combined_output.endswith("\n") else "\n")

    if result.returncode == 0:
        print("Expected the command to fail, but it exited successfully.")
        return 1

    missing_markers = [marker for marker in args.contains if marker not in combined_output]
    if missing_markers:
        print(
            f"Command failed with exit code {result.returncode}, "
            "but expected markers are missing:"
        )
        for marker in missing_markers:
            print(f"  - {marker!r}")
        return 1

    incorrect_counts: list[tuple[str, int, int]] = []
    for marker, expected_text in args.occurs:
        try:
            expected_count = int(expected_text)
        except ValueError:
            print(f"Invalid occurrence count {expected_text!r} for marker {marker!r}.")
            return 1
        actual_count = combined_output.count(marker)
        if actual_count != expected_count:
            incorrect_counts.append((marker, expected_count, actual_count))

    if incorrect_counts:
        print("Command failed, but output occurrence counts do not match:")
        for marker, expected_count, actual_count in incorrect_counts:
            print(f"  - {marker!r}: expected {expected_count}, found {actual_count}")
        return 1

    print(
        f"Verified expected failure: exit code {result.returncode}; "
        f"{len(args.contains)} marker(s) and {len(args.occurs)} count(s) matched."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
