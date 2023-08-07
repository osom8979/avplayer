# -*- coding: utf-8 -*-

from av.audio.stream import AudioStream
from av.stream import Stream
from av.video import VideoStream


def inject_go_faster_stream(stream: Stream) -> None:
    assert hasattr(stream, "thread_type")

    # https://ffmpeg.org/ffmpeg-codecs.html
    # Select which multithreading methods to use.
    # Use of ‘frame’ will increase decoding delay by one frame per thread,
    # so clients which cannot provide future frames should not use it.

    # av/codec/context.pyx
    # Possible values:
    # NONE = 0
    # FRAME = lib.FF_THREAD_FRAME
    #   Decode more than one frame at once.
    # SLICE = lib.FF_THREAD_SLICE
    #   Decode more than one part of a single frame at once.
    #   Multithreading using slices works only when the video was encoded with slices.
    # AUTO = lib.FF_THREAD_SLICE | lib.FF_THREAD_FRAME
    #   Either method (frame+slice)
    setattr(stream, "thread_type", "AUTO")


def inject_low_delay_stream(stream: Stream) -> None:
    assert hasattr(stream.codec_context, "flags")

    # av/codec/context.pyx
    # Possible values:
    # NONE = 0
    # UNALIGNED = lib.AV_CODEC_FLAG_UNALIGNED
    #    Allow decoders to produce frames with data planes that are not aligned
    #    to CPU requirements (e.g. due to cropping).
    # QSCALE = lib.AV_CODEC_FLAG_QSCALE
    #    Use fixed qscale.
    # 4MV = lib.AV_CODEC_FLAG_4MV
    #    4 MV per MB allowed / advanced prediction for H.263.
    # OUTPUT_CORRUPT = lib.AV_CODEC_FLAG_OUTPUT_CORRUPT
    #    Output even those frames that might be corrupted.
    # QPEL = lib.AV_CODEC_FLAG_QPEL
    #    Use qpel MC.
    # DROPCHANGED = 1 << 5
    #    Don't output frames whose parameters differ from first
    #    decoded frame in stream.
    # PASS1 = lib.AV_CODEC_FLAG_PASS1
    #    Use internal 2pass ratecontrol in first pass mode.
    # PASS2 = lib.AV_CODEC_FLAG_PASS2
    #    Use internal 2pass ratecontrol in second pass mode.
    # LOOP_FILTER = lib.AV_CODEC_FLAG_LOOP_FILTER
    #    loop filter.
    # GRAY = lib.AV_CODEC_FLAG_GRAY
    #    Only decode/encode grayscale.
    # PSNR = lib.AV_CODEC_FLAG_PSNR
    #    error[?] variables will be set during encoding.
    # TRUNCATED = lib.AV_CODEC_FLAG_TRUNCATED
    #    Input bitstream might be truncated at a random location
    #    instead of only at frame boundaries.
    # INTERLACED_DCT = lib.AV_CODEC_FLAG_INTERLACED_DCT
    #    Use interlaced DCT.
    # LOW_DELAY = lib.AV_CODEC_FLAG_LOW_DELAY
    #    Force low delay.
    # GLOBAL_HEADER = lib.AV_CODEC_FLAG_GLOBAL_HEADER
    #    Place global headers in extradata instead of every keyframe.
    # BITEXACT = lib.AV_CODEC_FLAG_BITEXACT
    #    Use only bitexact stuff (except (I)DCT).
    # AC_PRED = lib.AV_CODEC_FLAG_AC_PRED
    #    H.263 advanced intra coding / MPEG-4 AC prediction
    # INTERLACED_ME = lib.AV_CODEC_FLAG_INTERLACED_ME
    #    Interlaced motion estimation
    # CLOSED_GOP = lib.AV_CODEC_FLAG_CLOSED_GOP
    setattr(stream.codec_context, "flags", "LOW_DELAY")


def inject_speedup_tricks_stream(stream: Stream) -> None:
    assert hasattr(stream.codec_context, "flags2")

    # NONE = 0
    # FAST = lib.AV_CODEC_FLAG2_FAST
    #    Allow non-spec compliant speedup tricks.
    # NO_OUTPUT = lib.AV_CODEC_FLAG2_NO_OUTPUT
    #    Skip bitstream encoding.
    # LOCAL_HEADER = lib.AV_CODEC_FLAG2_LOCAL_HEADER
    #    Place global headers at every keyframe instead of in extradata.
    # DROP_FRAME_TIMECODE = lib.AV_CODEC_FLAG2_DROP_FRAME_TIMECODE
    #    Timecode is in drop frame format. DEPRECATED!!!!
    # CHUNKS = lib.AV_CODEC_FLAG2_CHUNKS
    #    Input bitstream might be truncated at a packet boundaries
    #    instead of only at frame boundaries.
    # IGNORE_CROP = lib.AV_CODEC_FLAG2_IGNORE_CROP
    #    Discard cropping information from SPS.
    # SHOW_ALL = lib.AV_CODEC_FLAG2_SHOW_ALL
    #    Show all frames before the first keyframe
    # EXPORT_MVS = lib.AV_CODEC_FLAG2_EXPORT_MVS
    #    Export motion vectors through frame side data
    # SKIP_MANUAL = lib.AV_CODEC_FLAG2_SKIP_MANUAL
    #    Do not skip samples and export skip information as frame side data
    # RO_FLUSH_NOOP = lib.AV_CODEC_FLAG2_RO_FLUSH_NOOP
    #    Do not reset ASS ReadOrder field on flush (subtitles decoding)
    setattr(stream.codec_context, "flags2", "FAST")


def set_stream_flags(
    stream: Stream,
    go_faster=False,
    low_delay=False,
    speedup_tricks=False,
) -> None:
    assert isinstance(stream, VideoStream) or isinstance(stream, AudioStream)

    if go_faster:
        inject_go_faster_stream(stream)
    if low_delay:
        inject_low_delay_stream(stream)
    if speedup_tricks:
        inject_speedup_tricks_stream(stream)
