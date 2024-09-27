# -*- coding: utf-8 -*-

from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from functools import lru_cache
from typing import Final, List, Optional

from avplayer.logging.logging import SEVERITIES, SEVERITY_NAME_INFO
from avplayer.variables import (
    APP_TYPES,
    DEFAULT_APP,
    DEFAULT_AV_OPEN_TIMEOUT,
    DEFAULT_AV_READ_TIMEOUT,
    DEFAULT_CV_EXIT_KEYS,
    DEFAULT_DROP_THRESHOLD,
    DEFAULT_IO_BUFFER_SIZE,
    DEFAULT_LOGGING_STEP,
    DEFAULT_WIN_FPS,
    DEFAULT_WIN_GEOMETRY,
    DEFAULT_WIN_QUEUE_SIZE,
    DEFAULT_WIN_TITLE,
)

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
        "--app-type",
        choices=APP_TYPES,
        default=DEFAULT_APP,
        help=f"Select app type (default: '{DEFAULT_APP}')",
    )

    parser.add_argument(
        "--ffmpeg-path",
        default="ffmpeg",
        metavar="path",
        help="FFmpeg command path",
    )
    parser.add_argument(
        "--logging-step",
        type=int,
        default=DEFAULT_LOGGING_STEP,
        metavar="size",
        help="An iterative step that emits statistics results to a logger",
    )

    parser.add_argument(
        "--severity",
        choices=SEVERITIES,
        default=SEVERITY_NAME_INFO,
        help=f"Logging severity (default: '{SEVERITY_NAME_INFO}')",
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
        "--input-size",
        "-is",
        default=None,
        metavar="{w}x{h}",
        help="Image size to pass to callback after decoding",
    )
    parser.add_argument(
        "--output-size",
        "-os",
        default=None,
        metavar="{w}x{h}",
        help="Size of image to encode",
    )

    parser.add_argument(
        "--timeout-open",
        default=DEFAULT_AV_OPEN_TIMEOUT,
        metavar="sec",
        type=float,
        help=f"AV IO open timeout seconds (default: {DEFAULT_AV_OPEN_TIMEOUT}s)",
    )
    parser.add_argument(
        "--timeout-read",
        default=DEFAULT_AV_READ_TIMEOUT,
        metavar="sec",
        type=float,
        help=f"AV IO read timeout seconds (default: {DEFAULT_AV_READ_TIMEOUT}s)",
    )
    parser.add_argument(
        "--buffer-size",
        type=int,
        default=DEFAULT_IO_BUFFER_SIZE,
        metavar="bytes",
        help=f"AV IO buffer size (default: {DEFAULT_IO_BUFFER_SIZE} bytes)",
    )

    parser.add_argument(
        "--drop-slow-frame",
        action="store_true",
        default=False,
        help="If consumption is slow, it will drop frames",
    )
    parser.add_argument(
        "--drop-threshold",
        type=int,
        default=DEFAULT_DROP_THRESHOLD,
        metavar="size",
        help="Threshold for the number of buffering to drop waiting frames",
    )

    parser.add_argument(
        "--win-geometry",
        default=DEFAULT_WIN_GEOMETRY,
        metavar="{w}x{h}+{x}+{y}",
        help=f"Tk window geometry (default: '{DEFAULT_WIN_GEOMETRY}')",
    )
    parser.add_argument(
        "--win-title",
        default=DEFAULT_WIN_TITLE,
        metavar="title",
        help=f"Tk/Cv window title (default: '{DEFAULT_WIN_TITLE}')",
    )
    parser.add_argument(
        "--win-fps",
        type=int,
        default=DEFAULT_WIN_FPS,
        metavar="fps",
        help=f"Tk window title (default: {DEFAULT_WIN_FPS})",
    )
    parser.add_argument(
        "--win-queue-size",
        type=int,
        default=DEFAULT_WIN_QUEUE_SIZE,
        metavar="size",
        help=f"Image queue size (default: {DEFAULT_WIN_QUEUE_SIZE})",
    )

    parser.add_argument(
        "--cv-flags",
        type=int,
        metavar="flags",
        help="Cv window flags (default: cv2.WINDOW_NORMAL)",
    )
    parser.add_argument(
        "--cv-exit-keys",
        action="extend",
        nargs="+",
        type=str,
        help=f"Cv exit codes (default: {DEFAULT_CV_EXIT_KEYS})",
    )
    parser.add_argument(
        "--cv-infinity",
        action="store_true",
        default=False,
        help="Enable infinite restart mode",
    )
    parser.add_argument(
        "--cv-headless",
        action="store_true",
        default=False,
        help="Hide cv2's highgui window",
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
