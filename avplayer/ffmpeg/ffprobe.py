# -*- coding: utf-8 -*-

from json import loads as json_loads
from subprocess import check_output
from typing import Any, Tuple


def inspect_source(src: str, ffprobe_path="ffprobe") -> Any:
    ffprobe_command = [
        ffprobe_path,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        src,
    ]
    output = check_output(ffprobe_command).decode("utf-8")
    return json_loads(output)


def inspect_source_size(
    src: str,
    ffprobe_path="ffprobe",
    video_stream_index=0,
) -> Tuple[int, int]:
    inspect_result = inspect_source(src, ffprobe_path)
    assert isinstance(inspect_result, dict)

    streams = inspect_result["streams"]
    video_streams = list(filter(lambda x: x["codec_type"] == "video", streams))
    video_stream = video_streams[video_stream_index]

    width = video_stream["width"]
    height = video_stream["height"]
    assert isinstance(width, int)
    assert isinstance(height, int)

    return width, height
