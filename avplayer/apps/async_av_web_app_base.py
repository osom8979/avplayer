# -*- coding: utf-8 -*-

from argparse import Namespace
from asyncio import Task, create_task
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import APIRouter, FastAPI
from numpy import uint8
from numpy.typing import NDArray
from overrides import override
from uvicorn import run as uvicorn_run

from avplayer.apps.async_av_app_base import AsyncAvAppBase
from avplayer.logging.logging import logger


class AsyncAvWebAppBase(AsyncAvAppBase):
    streamer_task: Task[None]

    def __init__(self, args: Namespace, printer: Callable[..., None] = print):
        super().__init__(args, printer)

        self._router = APIRouter()
        self._router.add_api_route("/health", self.health, methods=["GET"])

        self._app = FastAPI(lifespan=self._lifespan)
        self._app.include_router(self._router)

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        assert self._app == app
        self.streamer_task = create_task(self.async_run_streamer(), name="streamer")
        yield
        self.shutdown_streaming()
        await self.streamer_task

    @override
    async def on_image(self, image: NDArray[uint8]) -> NDArray[uint8]:
        return image

    @property
    def router(self):
        return self._router

    @property
    def app(self):
        return self._app

    async def health(self):
        streamer_task_name = self.streamer_task.get_name()
        streamer_task_live = not self.streamer_task.done()
        return {
            "tasks": {
                streamer_task_name: streamer_task_live,
            }
        }

    def run_streamer_with_webserver(self) -> None:
        uvicorn_run(
            self._app,
            host=self.bind,
            port=self.port,
            lifespan="on",
            log_level=logger.level,
        )
