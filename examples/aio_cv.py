# -*- coding: utf-8 -*-

from sys import argv
from datetime import datetime

import cv2
from numpy import uint8
from numpy.typing import NDArray

from avplayer import AioCv, AvConfig


def on_frame(frame: NDArray[uint8]):
    text = datetime.now().isoformat()
    ori = 10, 50
    font = cv2.FONT_HERSHEY_DUPLEX
    scale = 2.0
    color = 0, 255, 0
    thickness = 2
    cv2.putText(frame, text, ori, font, scale, color, thickness)
    return frame


def demo_main(url: str) -> None:
    app = AioCv(AvConfig(url, drop_slow_frame=True, drop_threshold=1), on_frame)
    app.start()


if __name__ == "__main__":
    demo_main(argv[1] if len(argv) >= 2 else "rtsp://localhost:8554/demo")
