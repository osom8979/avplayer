# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio.exceptions import CancelledError

from avplayer.apps.async_av_web_app_base import AsyncAvWebAppBase
from avplayer.logging.logging import logger


class DefaultApp(AsyncAvWebAppBase):
    def __init__(self, args: Namespace):
        super().__init__(args)


def default_main(args: Namespace) -> int:
    app = DefaultApp(args)

    try:
        app.run_webserver_with_avio()
    except CancelledError:
        logger.debug("An cancelled signal was detected")
        return 0
    except KeyboardInterrupt:
        logger.warning("An interrupt signal was detected")
        return 0
    except Exception as e:
        logger.exception(e)
        return 1
    except BaseException as e:
        logger.exception(e)
        return 1
    else:
        return 0
