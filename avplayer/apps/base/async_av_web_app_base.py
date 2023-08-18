# -*- coding: utf-8 -*-

from asyncio import Task, create_task
from contextlib import asynccontextmanager
from typing import Optional

from overrides import override

from avplayer.apps.base.async_av_app_base import AsyncAvAppBase
from avplayer.apps.interface.av_interface import AsyncAvInterface
from avplayer.avconfig import AvConfig
from avplayer.logging.logging import logger


class AsyncAvWebAppBase(AsyncAvAppBase):
    _avtask: Optional[Task[None]]

    def __init__(
        self,
        config: AvConfig,
        callback: Optional[AsyncAvInterface] = None,
        router=None,
    ):
        super().__init__(config, None)
        self._callback = callback

        from fastapi import APIRouter, FastAPI

        if router is not None:
            if not isinstance(router, APIRouter):
                raise TypeError("The 'router' must be of type fastapi.APIRouter")
            self._router = router
        else:
            self._router = APIRouter()
            self._router.add_api_route("/", self.health, methods=["GET"])

        self._app = FastAPI(lifespan=self._lifespan)
        self._app.include_router(self._router)

        self._avtask = None

    @property
    def router(self):
        return self._router

    @property
    def app(self):
        return self._app

    @asynccontextmanager
    async def _lifespan(self, app):
        assert self._app == app
        assert self._avtask is None
        if self._callback:
            await self._callback.on_open()
        self._avtask = create_task(self._until_thread_complete(), name="avtask")

        yield

        self._avio.shutdown()

        assert self._avtask is not None
        await self._avtask
        self._avtask = None

        if self._callback:
            await self._callback.on_close()

    async def health(self):
        assert self._avtask is not None
        avtask_name = self._avtask.get_name()
        avtask_live = not self._avtask.done()
        return {"tasks": {avtask_name: avtask_live}}

    @override
    def start(self) -> None:
        from uvicorn import run as uvicorn_run
        from uvicorn.config import LoopSetupType

        def get_loop_setup_type(use_uvloop: bool) -> LoopSetupType:
            if use_uvloop:
                return "uvloop"
            else:
                return "asyncio"

        uvicorn_run(
            self._app,
            host=self.config.bind,
            port=self.config.port,
            loop=get_loop_setup_type(self.config.use_uvloop),
            lifespan="on",
            log_level=logger.level,
        )
