# -*- coding: utf-8 -*-

from typing import Optional, Tuple

from av.audio.stream import AudioStream
from av.stream import Stream
from av.video import VideoStream

from avplayer.collections.frame_collection import FrameCollection
from avplayer.media.media_kind import MediaKind
from avplayer.variables import DEFAULT_FRAME_QUEUE_MAX


def inject_go_faster_stream(stream: Stream) -> None:
    assert hasattr(stream, "thread_type")
    setattr(stream, "thread_type", "AUTO")


def inject_low_delay_stream(stream: Stream) -> None:
    assert hasattr(stream.codec_context, "flags")
    setattr(stream.codec_context, "flags", "LOW_DELAY")


def init_stream(
    kind: MediaKind,
    index: Optional[int],
    streams,
    *,
    max_queue=DEFAULT_FRAME_QUEUE_MAX,
    go_faster=False,
    low_delay=False,
) -> Optional[Tuple[Stream, FrameCollection]]:
    assert kind in [MediaKind.Video, MediaKind.Audio]
    if index is None or index >= len(streams):
        return None

    assert index >= 0
    stream = streams[index]
    assert isinstance(stream, VideoStream) or isinstance(stream, AudioStream)

    if go_faster:
        inject_go_faster_stream(stream)
    if low_delay:
        inject_low_delay_stream(stream)

    return stream, FrameCollection(kind=kind, max_size=max_queue)
