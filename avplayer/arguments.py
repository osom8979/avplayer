# -*- coding: utf-8 -*-

from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from functools import lru_cache
from typing import Final, List, Optional

from avplayer.logging.logging import SEVERITIES, SEVERITY_NAME_INFO

PROG: Final[str] = "avplayer"
DESCRIPTION: Final[str] = "PyAV Media Player"
EPILOG = f"""
Examples:

    Play RTSP streaming sources:
        {PROG} -c -d rtsp://0.0.0.0:8554/live.sdp
"""


DEFAULT_SEVERITY: Final[str] = SEVERITY_NAME_INFO


@lru_cache
def version() -> str:
    # [IMPORTANT] Avoid 'circular import' issues
    from avplayer import __version__

    return __version__


def default_argument_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog=PROG,
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--colored-logging",
        "-c",
        action="store_true",
        default=False,
        help="Use colored logging",
    )
    parser.add_argument(
        "--simple-logging",
        "-s",
        action="store_true",
        default=False,
        help="Use simple logging",
    )
    parser.add_argument(
        "--severity",
        choices=SEVERITIES,
        default=DEFAULT_SEVERITY,
        help=f"Logging severity (default: '{DEFAULT_SEVERITY}')",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        default=False,
        help="Enable debugging mode and change logging severity to 'DEBUG'",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Be more verbose/talkative during the operation",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=version(),
    )

    parser.add_argument(
        "--output",
        "-o",
        help="AV output address",
    )
    parser.add_argument(
        "-io",
        action="extend",
        help="AV input options",
    )
    parser.add_argument(
        "-oo",
        action="extend",
        help="AV output options",
    )
    parser.add_argument(
        "source",
        help="AV source address",
    )
    return parser


def get_default_arguments(
    cmdline: Optional[List[str]] = None,
    namespace: Optional[Namespace] = None,
) -> Namespace:
    parser = default_argument_parser()
    return parser.parse_known_args(cmdline, namespace)[0]
