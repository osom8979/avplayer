# -*- coding: utf-8 -*-

from sys import exit as sys_exit
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
from avplayer.variables import PRINTER_NAMESPACE_ATTR_KEY


def main(
    cmdline: Optional[List[str]] = None,
    printer: Callable[..., None] = print,
) -> int:
    args = get_default_arguments(cmdline)

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

    assert not hasattr(args, PRINTER_NAMESPACE_ATTR_KEY)
    setattr(args, PRINTER_NAMESPACE_ATTR_KEY, printer)
    assert hasattr(args, PRINTER_NAMESPACE_ATTR_KEY)

    if colored_logging:
        set_colored_formatter_logging_config()
    elif simple_logging:
        set_simple_logging_config()

    if debug:
        set_root_level(SEVERITY_NAME_DEBUG)
    else:
        set_root_level(severity)

    logger.debug(f"Parsed arguments: {args}")
    return default_main(args)


if __name__ == "__main__":
    sys_exit(main())
