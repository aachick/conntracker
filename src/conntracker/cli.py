"""CLI functionalitiy."""
import argparse
import subprocess as sp
import sys

from typing import List, Optional, Sequence

from conntracker.__about__ import __version__
from conntracker.tracker import ConnTracker, warn_if_not_privileged


def main(args: Optional[Sequence[str]] = None) -> None:
    """CLI entrypoint for the monitor module."""
    warn_if_not_privileged()

    parser = argparse.ArgumentParser(
        prog="nettracker",
        description="Track socket connections opened by a program.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--ignore-children",
        action="store_true",
        help="If set, don't track connections opened by child processes (default: %(default)s).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="",
        help="If set, write tracker results to the specified file.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=__version__,
        help="Print the program version and exit.",
    )
    parser.add_argument(
        "program",
        nargs=argparse.REMAINDER,
        help=(
            "The program and its options/arguments. Examples:\n"
            "  python script.py\n"
            "  python script2.py -n 20 -foo bar"
        ),
    )

    arg_values = parser.parse_args(args=args)

    prog: List[str] = arg_values.program
    if len(prog) < 1:
        parser.exit(status=1, message="No program was given to execute.")

    with sp.Popen(prog) as pipe:
        tracker = ConnTracker(pid=pipe.pid, track_children=not arg_values.ignore_children)
        retval: Optional[int] = None
        with tracker:
            while retval is None:
                retval = pipe.poll()

        tracker_str = repr(tracker)
        if arg_values.output:
            with open(arg_values.output, "w", encoding="utf-8") as out:
                out.write(tracker_str)
        else:
            sys.stdout.write(tracker_str)

    sys.exit(retval)


if __name__ == "__main__":
    main()
