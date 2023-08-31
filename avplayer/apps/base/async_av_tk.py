# -*- coding: utf-8 -*-

from typing import Optional

from overrides import override

from avplayer.aio.run import aio_run
from avplayer.apps.base.async_av_app import AsyncAvApp
from avplayer.apps.interface.av_interface import AsyncAvInterface
from avplayer.avconfig import AvConfig


class AsyncAvTk(AsyncAvApp):
    _callback: Optional[AsyncAvInterface]  # type: ignore[assignment]

    def __init__(self, config: AvConfig, callback: Optional[AsyncAvInterface] = None):
        super().__init__(config, callback)

    @override
    def start(self) -> None:
        aio_run(
            self._event_context_with_until_thread_complete(),
            self.config.use_uvloop,
        )
