# -*- coding: utf-8 -*-

from asyncio import Task, create_task
from contextlib import asynccontextmanager
from typing import Optional

from avplayer.apps.base.async_av_app_base import AsyncAvAppBase
from avplayer.apps.interface.async_av_interface import AsyncAvWebInterface
from avplayer.config import Config
from avplayer.logging.logging import logger


class AsyncAvWebAppBase(AsyncAvAppBase):
    _callback: Optional[AsyncAvWebInterface]  # type: ignore[assignment]
    _avio_task: Optional[Task[None]]

    def __init__(self, config: Config, callback: Optional[AsyncAvWebInterface] = None):
        super().__init__(config, None)
        self._callback = callback

        from fastapi import APIRouter, FastAPI

        GET = "GET"  # noqa
        POST = "POST"  # noqa

        self._router = APIRouter()
        self._router.add_api_route("/health", self.health, methods=[GET])
        self._router.add_api_route("/keypressed", self.keypressed, methods=[POST])

        self._app = FastAPI(lifespan=self._lifespan)
        self._app.include_router(self._router)

        self._avio_task = None

    @property
    def router(self):
        return self._router

    @property
    def app(self):
        return self._app

    @asynccontextmanager
    async def _lifespan(self, app):
        assert self._app == app
        assert self._avio_task is None
        self._avio_task = create_task(self.start_async_app(), name="avio")

        yield

        self.shutdown_avio()

        assert self._avio_task is not None
        await self._avio_task
        self._avio_task = None

    async def health(self):
        assert self._avio_task is not None
        avio_task_name = self._avio_task.get_name()
        avio_task_live = not self._avio_task.done()
        return {
            "tasks": {
                avio_task_name: avio_task_live,
            }
        }

    async def keypressed(self, keycode: str, shift=False, ctrl=False, alt=False):
        if self._callback is None:
            return

        await self._callback.on_key_pressed(
            keycode=keycode,
            shift=shift,
            ctrl=ctrl,
            alt=alt,
        )

    def start_webserver_with_avio(self) -> None:
        from uvicorn import run

        run(
            self._app,
            host=self.config.bind,
            port=self.config.port,
            lifespan="on",
            log_level=logger.level,
        )
