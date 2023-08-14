# -*- coding: utf-8 -*-

from io import StringIO
from os import path
from subprocess import check_output
from typing import Final, List, NamedTuple
from urllib.parse import urlparse

from avplayer.ffmpeg.ffmpeg_formats import FFMPEG_FORMATS
from avplayer.ffmpeg.ffmpeg_pix_fmts import FFMPEG_PIX_FMTS

BGR24_CHANNELS: Final[int] = 3
MINIMUM_REALTIME_FRAMES: Final[int] = 12
MEGA_BYTE_UNIT: Final[int] = 1024 * 1024
DEFAULT_BUFFER_SIZE: Final[int] = 100 * MEGA_BYTE_UNIT

PRESET_ULTRAFAST: Final[str] = "ultrafast"
PRESET_SUPERFAST: Final[str] = "superfast"
PRESET_VERYFAST: Final[str] = "veryfast"
PRESET_FASTER: Final[str] = "faster"
PRESET_FAST: Final[str] = "fast"
PRESET_MEDIUM: Final[str] = "medium"
PRESET_PRESET: Final[str] = "preset"
PRESET_SLOW: Final[str] = "slow"
PRESET_SLOWER: Final[str] = "slower"
PRESET_VERYSLOW: Final[str] = "veryslow"
PRESET_PLACEBO: Final[str] = "placebo"  # ignore this as it is not useful
PRESET_DEFAULT: Final[str] = PRESET_MEDIUM

CRF_LOSSLESS: Final[int] = 0  # for 8 bit only, for 10 bit use -qp 0
CRF_VISUALLY_LOSSLESS: Final[int] = 17
CRF_DEFAULT: Final[int] = 23
CRF_WORST_QUALITY_POSSIBLE: Final[int] = 51
CRF_MIN: Final[int] = CRF_LOSSLESS
CRF_MAX: Final[int] = CRF_WORST_QUALITY_POSSIBLE
CRF_SANE_RANGE_MIN: Final[int] = 17
CRF_SANE_RANGE_MAX: Final[int] = 28

# https://trac.ffmpeg.org/wiki/Encode/H.264#Tune
TUNE_FILM: Final[str] = "film"
TUNE_ANIMATION: Final[str] = "animation"
TUNE_GRAIN: Final[str] = "grain"
TUNE_STILLIMAGE: Final[str] = "stillimage"
TUNE_FASTDECODE: Final[str] = "fastdecode"
TUNE_ZEROLATENCY: Final[str] = "zerolatency"
TUNE_PSNR: Final[str] = "psnr"
TUNE_SSIM: Final[str] = "ssim"

# https://trac.ffmpeg.org/wiki/Encode/H.264#Profile
PROFILE_BASELINE: Final[str] = "baseline"
PROFILE_MAIN: Final[str] = "main"
PROFILE_HIGH: Final[str] = "high"
PROFILE_HIGH10: Final[str] = "high10"
PROFILE_HIGH422: Final[str] = "high422"
PROFILE_HIGH444: Final[str] = "high444"

# List presets and tunes
# ffmpeg -hide_banner -f lavfi -i nullsrc -c:v libx264 -preset help -f mp4 -

AUTOMATIC_DETECT_FILE_FORMAT: Final[str] = "autodect"
DEFAULT_PIXEL_FORMAT: Final[str] = "bgr24"
DEFAULT_FILE_FORMAT: Final[str] = AUTOMATIC_DETECT_FILE_FORMAT

FFMPEG_PIX_FMTS_HEADER_LINES: Final[int] = 8
"""
Skip unnecessary header lines in `ffmpeg -hide_banner -pix_fmts` command.
Perhaps something like this:

```
Pixel formats:
I.... = Supported Input  format for conversion
.O... = Supported Output format for conversion
..H.. = Hardware accelerated format
...P. = Paletted format
....B = Bitstream format
FLAGS NAME            NB_COMPONENTS BITS_PER_PIXEL
-----
```

For reference, the next line would look something like this:

```
IO... yuv420p                3            12
IO... yuyv422                3            16
IO... rgb24                  3            24
IO... bgr24                  3            24
IO... yuv422p                3            16
IO... yuv444p                3            24
IO... yuv410p                3             9
IO... yuv411p                3            12
IO... gray                   1             8
```
"""


class PixFmt(NamedTuple):
    supported_input_format: bool
    supported_output_format: bool
    hardware_accelerated_format: bool
    paletted_format: bool
    bitstream_format: bool
    name: str
    nb_components: int
    bits_per_pixel: int

    def __repr__(self):
        buffer = StringIO()
        buffer.write("I" if self.supported_input_format else ".")
        buffer.write("O" if self.supported_output_format else ".")
        buffer.write("H" if self.hardware_accelerated_format else ".")
        buffer.write("P" if self.paletted_format else ".")
        buffer.write("B" if self.bitstream_format else ".")
        buffer.write(f" comp={self.nb_components}")
        buffer.write(f" bits={self.bits_per_pixel:<3}")
        buffer.write(f" {self.name}")
        return buffer.getvalue()


def inspect_pix_fmts(ffmpeg_path="ffmpeg") -> List[PixFmt]:
    try:
        cmds = [ffmpeg_path, "-hide_banner", "-pix_fmts"]
        output = check_output(cmds).decode("utf-8")
    except:  # noqa
        output = FFMPEG_PIX_FMTS
    lines = output.splitlines()[FFMPEG_PIX_FMTS_HEADER_LINES:]

    result = list()
    for line in lines:
        cols = [c.strip() for c in line.split()]
        assert len(cols) == 4
        flags = cols[0]
        fmt = PixFmt(
            supported_input_format=(flags[0] == "I"),
            supported_output_format=(flags[1] == "O"),
            hardware_accelerated_format=(flags[2] == "H"),
            paletted_format=(flags[3] == "P"),
            bitstream_format=(flags[4] == "B"),
            name=cols[1],
            nb_components=int(cols[2]),
            bits_per_pixel=int(cols[3]),
        )
        result.append(fmt)
    return result


def find_pix_fmt(pixel_format: str, ffmpeg_path="ffmpeg") -> PixFmt:
    pix_fmts = inspect_pix_fmts(ffmpeg_path)
    filtered_pix_fmts = list(filter(lambda x: x.name == pixel_format, pix_fmts))
    if not filtered_pix_fmts:
        raise IndexError(f"Not found pixel format: {pixel_format}")
    assert len(filtered_pix_fmts) == 1
    return filtered_pix_fmts[0]


def find_bits_per_pixel(pixel_format: str, ffmpeg_path="ffmpeg") -> int:
    return find_pix_fmt(pixel_format, ffmpeg_path).bits_per_pixel


WELL_KNOWN_SCHEME_FORMAT: Final[dict] = {
    "rtmp": "flv",
    "rtsp": "rtsp",
}
FFMPEG_FILE_FORMATS_HEADER_LINES: Final[int] = 4
"""
Skip unnecessary header lines in `ffmpeg -hide_banner -formats` command.
Perhaps something like this:

```
File formats:
 D. = Demuxing supported
 .E = Muxing supported
 --
```

For reference, the next line would look something like this:

```
 D  3dostr          3DO STR
  E 3g2             3GP2 (3GPP2 file format)
  E 3gp             3GP (3GPP file format)
 D  4xm             4X Technologies
  E a64             a64 - video for Commodore 64
 D  aa              Audible AA format files
 D  aac             raw ADTS AAC (Advanced Audio Coding)
 D  aax             CRI AAX
 DE ac3             raw AC-3
```
"""


class FileFormat(NamedTuple):
    supported_demuxing: bool
    supported_muxing: bool
    name: str
    description: str

    def __repr__(self):
        buffer = StringIO()
        buffer.write("D" if self.supported_demuxing else ".")
        buffer.write("E" if self.supported_muxing else ".")
        buffer.write(f" {self.name}")
        return buffer.getvalue()


def inspect_file_formats(ffmpeg_path="ffmpeg") -> List[FileFormat]:
    try:
        cmds = [ffmpeg_path, "-hide_banner", "-formats"]
        output = check_output(cmds).decode("utf-8")
    except:  # noqa
        output = FFMPEG_FORMATS
    lines = output.splitlines()[FFMPEG_FILE_FORMATS_HEADER_LINES:]

    result = list()
    for line in lines:
        supported_demuxing = line[1] == "D"
        supported_muxing = line[2] == "E"
        name_desc = line[4:].split(maxsplit=1)
        name = name_desc[0]
        desc = name_desc[1] if len(name_desc) == 2 else str()
        fmt = FileFormat(
            supported_demuxing=supported_demuxing,
            supported_muxing=supported_muxing,
            name=name,
            description=desc,
        )
        result.append(fmt)
    return result


def detect_file_format(url: str, ffmpeg_path="ffmpeg") -> str:
    if path.exists(url):
        ext = path.splitext(url)[1]
        return ext[1:] if ext[0] == "." else ext
    else:
        file_formats = inspect_file_formats(ffmpeg_path)
        o = urlparse(url)
        if o.scheme:
            if o.scheme in WELL_KNOWN_SCHEME_FORMAT:
                return WELL_KNOWN_SCHEME_FORMAT[o.scheme]
            try:
                file_format = next(filter(lambda f: f.name == o.scheme, file_formats))
            except StopIteration:
                raise IndexError(f"Unsupported URL scheme: {o.scheme}")
            else:
                return file_format.name
        else:
            raise NotImplementedError("URL scheme is required")


def calc_recommend_buffer_size(
    width: int,
    height: int,
    channels=BGR24_CHANNELS,
    frames=MINIMUM_REALTIME_FRAMES,
) -> int:
    assert channels >= 1
    assert frames >= 1
    return width * height * channels * frames


def calc_minimum_buffer_size(
    width: int,
    height: int,
    channels=BGR24_CHANNELS,
    frames=MINIMUM_REALTIME_FRAMES,
) -> int:
    recommend_size = calc_recommend_buffer_size(width, height, channels, frames)
    return min(DEFAULT_BUFFER_SIZE, recommend_size)
