# -*- coding: utf-8 -*-

from functools import reduce
from io import StringIO
from typing import Any, Iterable, List, Optional, Tuple, Union, get_args

from avplayer.m3u.m3u_tags import (
    EXT_X_DEFINE,
    EXT_X_DISCONTINUITY_SEQUENCE,
    EXT_X_ENDLIST,
    EXT_X_INDEPENDENT_SEGMENTS,
    EXT_X_KEY,
    EXT_X_MEDIA_SEQUENCE,
    EXT_X_START,
    EXT_X_STREAM_INF,
    EXT_X_TARGETDURATION,
    EXT_X_VERSION,
    EXTINF,
    EXTM3U,
    ExtXKey_MethodLiteral,
    ExtXStreamInf_HdcpLevelLiteral,
    ExtXStreamInf_VideoRangeLiteral,
    ExtXVersionLiteral,
)

_required = object()
_no_quoting = object()
_append_comma = object()


def _raise_enum_error(name: str, literal_cls):
    raise ValueError(
        f"The `{name}` argument must be one of the following values:"
        f"{get_args(literal_cls)}"
    )


class M3uBuilder:
    def __init__(self, master: Optional[bool] = None):
        self._master = master
        self._lines: List[str] = list()

    def done(self) -> str:
        buffer = StringIO()
        for line in self._lines:
            if not line:
                buffer.write("\n")
                continue
            if line[-1] == "\n":
                buffer.write(line)
            else:
                buffer.write(line + "\n")
        return buffer.getvalue().strip()

    def write(self, line: str) -> "M3uBuilder":
        self._lines.append(line.strip())
        return self

    def newline(self):
        return self.write("\n")

    @staticmethod
    def make_attribute_list(
        tag: str,
        *attribute_list: Optional[Tuple[str, Any]],
    ) -> str:
        buffer = StringIO()

        for attribute in attribute_list:
            if attribute is None:
                continue

            assert len(attribute) >= 2
            key = attribute[0]
            val = attribute[1]
            assert key

            if len(attribute) >= 3:
                flags = attribute[2:]
                no_quoting = _no_quoting in flags
                required = _required in flags
            else:
                no_quoting = False
                required = False

            if val is None:
                if required:
                    raise ValueError(f"The `{key}` value of `{tag}` is REQUIRED")
                else:
                    continue

            if buffer.tell():
                buffer.write(",")

            if isinstance(val, bool):
                boolean_val = "YES" if val else "NO"
                buffer.write(f"{key}={boolean_val}")
            elif isinstance(val, str):
                if no_quoting:
                    buffer.write(f"{key}={val}")
                else:
                    buffer.write(f'{key}="{val}"')
            else:
                buffer.write(f"{key}={val}")

        if buffer.tell():
            return f"{tag}:{buffer.getvalue()}"
        else:
            return tag

    def write_attribute_list(self, tag: str, *attribute_list):
        return self.write(self.make_attribute_list(tag, *attribute_list))

    # ----------
    # Basic Tags
    # ----------

    def extm3u(self):
        return self.write(EXTM3U)

    def ext_x_version(self, n: Union[int, ExtXVersionLiteral]):
        return self.write(f"{EXT_X_VERSION}:{n}")

    # -----------------------------
    # Media or Master Playlist Tags
    # -----------------------------

    def ext_x_independent_segments(self):
        return self.write(EXT_X_INDEPENDENT_SEGMENTS)

    def ext_x_start(
        self,
        time_offset: Optional[float] = None,
        precise: Optional[bool] = None,
    ):
        return self.write_attribute_list(
            EXT_X_START,
            ("TIME-OFFSET", time_offset),
            ("PRECISE", precise),
        )

    def ext_x_define(
        self,
        name: Optional[str] = None,
        value: Optional[str] = None,
        import_: Optional[str] = None,
    ):
        if name is not None and value is None:
            raise ValueError("If `name` exists, then `value` must also exist")
        if name is None and value is not None:
            raise ValueError(
                "If `name` does not exist then `value` must not exist either"
            )

        if self._master and import_ is not None:
            raise ValueError("`IMPORT` attribute MUST NOT occur in master playlists")

        return self.write_attribute_list(
            EXT_X_DEFINE,
            ("NAME", name),
            ("VALUE", value),
            ("IMPORT", import_),
        )

    # -------------------
    # Media Playlist Tags
    # -------------------

    def ext_x_targetduration(self, s: int):
        return self.write(f"{EXT_X_TARGETDURATION}:{s}")

    def ext_x_media_sequence(self, number: int):
        return self.write(f"{EXT_X_MEDIA_SEQUENCE}:{number}")

    def ext_x_discontinuity_sequence(self, number: int):
        return self.write(f"{EXT_X_DISCONTINUITY_SEQUENCE}:{number}")

    def ext_x_endlist(self):
        return self.write(EXT_X_ENDLIST)

    def ext_x_playlist_type(self):
        raise NotImplementedError

    def ext_x_i_frames_only(self):
        raise NotImplementedError

    def ext_x_part_inf(self):
        raise NotImplementedError

    def ext_x_server_control(self):
        raise NotImplementedError

    # ------------------
    # Media Segment Tags
    # ------------------

    def extinf(self, duration: float, title: Optional[str] = None):
        if title:
            return self.write(f"{EXTINF}:{duration},{title}")
        else:
            # In the spec, must include commas(',').
            return self.write(f"{EXTINF}:{duration},")

    def extinf_uri(self, uri: str, *args, **kwargs):
        return self.extinf(*args, **kwargs).write(uri)

    def ext_x_byterange(self):
        raise NotImplementedError

    def ext_x_discontinuity(self):
        raise NotImplementedError

    def ext_x_key(
        self,
        method: Union[str, ExtXKey_MethodLiteral],
        uri: Optional[str] = None,
        iv: Optional[str] = None,
        keyformat: Optional[str] = None,
        keyformatversions: Optional[str] = None,
    ):
        if method not in get_args(ExtXKey_MethodLiteral):
            _raise_enum_error("method", ExtXKey_MethodLiteral)

        if method != "NONE" and not uri:
            raise ValueError(
                "The `URI` attribute is REQUIRED unless the METHOD is NONE"
            )

        return self.write_attribute_list(
            EXT_X_KEY,
            ("METHOD", method, _required, _no_quoting),
            ("URI", uri),
            ("IV", iv),  # hexadecimal-sequence 128-bit
            ("KEYFORMAT", keyformat),
            ("KEYFORMATVERSIONS", keyformatversions),
        )

    def ext_x_map(self):
        raise NotImplementedError

    def ext_x_program_date_time(self):
        raise NotImplementedError

    def ext_x_gap(self):
        raise NotImplementedError

    def ext_x_bitrate(self):
        raise NotImplementedError

    def ext_x_part(self):
        raise NotImplementedError

    # -------------------
    # Media Metadata Tags
    # -------------------

    def ext_x_daterange(self):
        raise NotImplementedError

    def ext_x_skip(self):
        raise NotImplementedError

    def ext_x_preload_hint(self):
        raise NotImplementedError

    def ext_x_rendition_report(self):
        raise NotImplementedError

    # --------------------
    # Master Playlist Tags
    # --------------------

    def ext_x_media(self):
        raise NotImplementedError

    def ext_x_stream_inf(
        self,
        bandwidth: int,
        average_bandwidth: Optional[int] = None,
        score: Optional[float] = None,
        codecs: Optional[Iterable[str]] = None,
        resolution: Optional[Tuple[int, int]] = None,
        frame_rate: Optional[float] = None,
        hdcp_level: Optional[Union[str, ExtXStreamInf_HdcpLevelLiteral]] = None,
        allowed_cpc: Optional[str] = None,
        video_range: Optional[Union[str, ExtXStreamInf_VideoRangeLiteral]] = None,
        stable_variant_id: Optional[str] = None,
        audio: Optional[str] = None,
        video: Optional[str] = None,
        subtitles: Optional[str] = None,
        closed_captions: Optional[str] = None,
    ):
        if hdcp_level and hdcp_level not in get_args(ExtXStreamInf_HdcpLevelLiteral):
            _raise_enum_error("hdcp_level", ExtXStreamInf_HdcpLevelLiteral)
        if video_range and video_range not in get_args(ExtXStreamInf_VideoRangeLiteral):
            _raise_enum_error("video_range", ExtXStreamInf_VideoRangeLiteral)

        if codecs:
            merged_codecs = reduce(lambda x, y: x + "," + y, codecs)
        else:
            merged_codecs = None

        if resolution:
            assert len(resolution) == 2
            merged_resolution = f"{resolution[0]}x{resolution[1]}"
        else:
            merged_resolution = None

        return self.write_attribute_list(
            EXT_X_STREAM_INF,
            ("BANDWIDTH", bandwidth, _required),
            ("AVERAGE-BANDWIDTH", average_bandwidth),
            ("SCORE", score),
            ("CODECS", merged_codecs if merged_codecs else None),  # SHOULD
            ("RESOLUTION", merged_resolution, _no_quoting),
            ("FRAME-RATE", frame_rate),
            ("HDCP-LEVEL", hdcp_level, _no_quoting),
            ("ALLOWED-CPC", allowed_cpc),
            ("VIDEO-RANGE", video_range, _no_quoting),
            ("STABLE-VARIANT-ID", stable_variant_id),
            ("AUDIO", audio),
            ("VIDEO", video),
            ("SUBTITLES", subtitles),
            ("CLOSED-CAPTIONS", closed_captions),
        )

    def ext_x_stream_inf_uri(self, uri: str, *args, **kwargs):
        return self.ext_x_stream_inf(*args, **kwargs).write(uri)

    def ext_x_i_frame_stream_inf(self):
        raise NotImplementedError

    def ext_x_session_data(self):
        raise NotImplementedError

    def ext_x_session_key(self):
        raise NotImplementedError


def extm3u(master: Optional[bool] = None) -> M3uBuilder:
    return M3uBuilder(master).extm3u()
