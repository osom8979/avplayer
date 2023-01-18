# -*- coding: utf-8 -*-

from sys import exit as sys_exit
from sys import stderr
from typing import Callable, List, Optional

from avplayer.apps.default import default_main
from avplayer.arguments import get_default_arguments
from avplayer.logging.logging import (
    SEVERITY_NAME_DEBUG,
    logger,
    set_colored_formatter_logging_config,
    set_root_level,
    set_simple_logging_config,
)


def main(
    cmdline: Optional[List[str]] = None,
    printer: Callable[..., None] = print,
) -> int:
    args = get_default_arguments(cmdline)

    if args.colored_logging and args.simple_logging:
        _msg = "The 'colored_logging' flag and the 'simple_logging' flag cannot coexist"
        printer(_msg, file=stderr)
        return 1

    colored_logging = args.colored_logging
    simple_logging = args.simple_logging
    severity = args.severity
    debug = args.debug
    verbose = args.verbose

    assert isinstance(colored_logging, bool)
    assert isinstance(simple_logging, bool)
    assert isinstance(severity, str)
    assert isinstance(debug, bool)
    assert isinstance(verbose, int)

    if colored_logging:
        set_colored_formatter_logging_config()
    elif simple_logging:
        set_simple_logging_config()

    if debug:
        set_root_level(SEVERITY_NAME_DEBUG)
    else:
        set_root_level(severity)

    logger.debug(f"Arguments: {args}")

    try:
        default_main(args)
        return 0
    except BaseException as e:
        logger.exception(e)
        return 1


if __name__ == "__main__":
    sys_exit(main())
