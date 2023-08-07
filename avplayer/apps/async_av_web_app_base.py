# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio import Task, create_task
from contextlib import asynccontextmanager
from typing import Callable, Optional

from fastapi import APIRouter, FastAPI
from numpy import uint8
from numpy.typing import NDArray
from overrides import override
from uvicorn import run as uvicorn_run

from avplayer.apps.async_av_app_base import AsyncAvAppBase
from avplayer.logging.logging import logger


class AsyncAvWebAppBase(AsyncAvAppBase):
    _avio_task: Optional[Task[None]]

    def __init__(self, args: Namespace, printer: Callable[..., None] = print):
        super().__init__(args, printer)

        self._router = APIRouter()
        self._router.add_api_route("/health", self.health, methods=["GET"])

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
    async def _lifespan(self, app: FastAPI):
        assert self._app == app
        assert self._avio_task is None
        self._avio_task = create_task(self.async_run_avio(), name="avio")

        yield

        self.shutdown_avio()

        assert self._avio_task is not None
        await self._avio_task
        self._avio_task = None

    @override
    async def on_image(self, image: NDArray[uint8]) -> NDArray[uint8]:
        return image

    async def health(self):
        assert self._avio_task is not None
        avio_task_name = self._avio_task.get_name()
        avio_task_live = not self._avio_task.done()
        return {
            "tasks": {
                avio_task_name: avio_task_live,
            }
        }

    def run_webserver_with_avio(self) -> None:
        uvicorn_run(
            self._app,
            host=self.bind,
            port=self.port,
            lifespan="on",
            log_level=logger.level,
        )
