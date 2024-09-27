# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio.exceptions import CancelledError

from avplayer.apps.base.base import AppInterface
from avplayer.apps.defaults import AioApp, AioCv, AioTk, IoApp
from avplayer.avconfig import AvAppType, AvConfig
from avplayer.logging.logging import logger


def create_app(config: AvConfig, coro=None) -> AppInterface:
    app_type = config.app_type
    if app_type == AvAppType.IO:
        return IoApp(config, coro)
    elif app_type == AvAppType.AIO:
        return AioApp(config, coro)
    elif app_type == AvAppType.AIOTK:
        return AioTk(config, coro)
    elif app_type == AvAppType.CV:
        return AioCv(config, coro)
    else:
        raise ValueError(f"Unknown app type: {app_type}")


def default_main_with_config(config: AvConfig, coro=None) -> int:
    app = create_app(config, coro)
    try:
        app.start()
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


def av_main(args: Namespace, coro=None) -> int:
    config = AvConfig.from_namespace(args)
    config.logging_params()
    return default_main_with_config(config, coro)
