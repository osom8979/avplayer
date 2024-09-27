# -*- coding: utf-8 -*-

import sys

import cv2

from avplayer.apps.base.async_av_app import AsyncAvApp, AsyncAvInterface, AvConfig


class CvExample(AsyncAvApp, AsyncAvInterface):
    def __init__(self, title: str, src: str):
        super().__init__(AvConfig(input_file=src, drop_slow_frame=True), callback=self)
        self._title = title

    async def on_open(self) -> None:
        pass

    async def on_close(self) -> None:
        pass

    async def on_image(self, image):
        # TODO: Implement your code here.

        cv2.imshow(self._title, image)
        if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
            self.avio.done()


def demo_main(url: str, title="Demo") -> None:
    # [IMPORTANT]
    # You must call cv2's highgui before avplayer.
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)

    try:
        player = CvExample(title, url)
        player.start()
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    demo_main(sys.argv[1] if len(sys.argv) >= 2 else "rtsp://localhost:8554/demo")
