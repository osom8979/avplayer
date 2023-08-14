# -*- coding: utf-8 -*-

from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from functools import lru_cache
from typing import Final, List, Optional

from avplayer.logging.logging import SEVERITIES, SEVERITY_NAME_INFO

PROG: Final[str] = "avplayer"
DESCRIPTION: Final[str] = "PyAV Media Player"
EPILOG = f"""
Examples:

  Debugging flags:
    {PROG} -c -d -vv ...

  Play RTSP streaming sources:
    {PROG} rtsp://localhost:8554/live.sdp

  RTSP to RTSP Demo:
    docker run --rm -it -e RTSP_PORT=9999 -p 9999:9999 ullaakut/rtspatt
    docker run --rm -it -e MTX_PROTOCOLS=tcp -p 8554:8554 bluenviron/mediamtx
    {PROG} -c -d -vv -o rtsp://localhost:8554/live rtsp://localhost:9999/live.sdp
    ffplay rtsp://localhost:8554/live
"""

DEFAULT_SEVERITY: Final[str] = SEVERITY_NAME_INFO
DEFAULT_BIND: Final[str] = "0.0.0.0"
DEFAULT_PORT: Final[int] = 8080
DEFAULT_TIMEOUT: Final[float] = 8.0
DEFAULT_LOGGING_STEP: Final[int] = 1000


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

    logging_group = parser.add_mutually_exclusive_group()
    logging_group.add_argument(
        "--colored-logging",
        "-c",
        action="store_true",
        default=False,
        help="Use colored logging",
    )
    logging_group.add_argument(
        "--simple-logging",
        "-s",
        action="store_true",
        default=False,
        help="Use simple logging",
    )

    parser.add_argument(
        "--use-uvloop",
        action="store_true",
        default=False,
        help="Replace the event loop with uvloop",
    )

    parser.add_argument(
        "--ffmpeg-path",
        default="ffmpeg",
        help="FFmpeg command path",
    )
    parser.add_argument(
        "--ffprobe-path",
        default="ffprobe",
        help="FFprobe command path",
    )
    parser.add_argument(
        "--logging-step",
        type=int,
        default=DEFAULT_LOGGING_STEP,
        help="An iterative step that emits statistics results to a logger",
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
        "--bind",
        "-b",
        default=DEFAULT_BIND,
        metavar="bind",
        help=f"Bind address (default: '{DEFAULT_BIND}')",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=DEFAULT_PORT,
        metavar="port",
        help=f"Port number (default: '{DEFAULT_PORT}')",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        default=DEFAULT_TIMEOUT,
        type=float,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )

    parser.add_argument(
        "--input-size",
        "-is",
        default=None,
        metavar="WxH",
        help="Source Size",
    )
    parser.add_argument(
        "--output-size",
        "-os",
        default=None,
        metavar="WxH",
        help="Destination Size",
    )

    parser.add_argument(
        "--output",
        "-o",
        default="",
        help="AV output address",
    )
    parser.add_argument(
        "input",
        help="AV input address",
    )

    return parser


def get_default_arguments(
    cmdline: Optional[List[str]] = None,
    namespace: Optional[Namespace] = None,
) -> Namespace:
    parser = default_argument_parser()
    return parser.parse_known_args(cmdline, namespace)[0]
