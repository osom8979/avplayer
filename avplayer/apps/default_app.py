# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio.exceptions import CancelledError
from typing import Optional

from numpy import uint8
from numpy.typing import NDArray
from overrides import override

from avplayer.apps.base.av_app_base import AvAppBase
from avplayer.apps.interface.av_interface import AvInterface
from avplayer.logging.logging import logger


class DefaultApp(AvAppBase, AvInterface):
    def __init__(self, args: Namespace):
        super().__init__(args, self)

    @override
    def on_image(self, image: NDArray[uint8]) -> Optional[NDArray[uint8]]:
        return image


def default_app_main(args: Namespace) -> int:
    app = DefaultApp(args)
    try:
        app.start_app()
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
