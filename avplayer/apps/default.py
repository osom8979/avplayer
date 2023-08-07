# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio.exceptions import CancelledError
from typing import Callable

from numpy import uint8
from numpy.typing import NDArray
from overrides import override

from avplayer.apps.async_av_web_app_base import AsyncAvWebAppBase
from avplayer.logging.logging import logger


class DefaultApp(AsyncAvWebAppBase):
    def __init__(self, args: Namespace, printer: Callable[..., None] = print):
        super().__init__(args, printer)

    @override
    async def on_image(self, image: NDArray[uint8]) -> NDArray[uint8]:
        return image


def default_main(args: Namespace, printer: Callable[..., None] = print) -> int:
    app = DefaultApp(args, printer)

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
