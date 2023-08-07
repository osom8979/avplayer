# -*- coding: utf-8 -*-

import os
from dataclasses import dataclass, field
from tempfile import mkdtemp
from typing import Any, Dict, Literal, Union

from avplayer.variables import HLS_MASTER_FILENAME, HLS_SEGMENT_FILENAME


@dataclass
class HlsOutputAvOptions:
    destination_dir: str
    """Local directory to store processed segmentation files.
    """

    cache_dir: str = field(default_factory=lambda: mkdtemp())
    """Cache directory for temporarily storing HLS segmentation files.
    """

    strftime: bool = True
    """Use strftime() on filename to expand the segment filename with localtime.
    """

    strftime_mkdir: bool = True
    """It will create all subdirectories which is expanded in filename.
    """

    hls_time: int = 10
    """Set the target segment length.
    """

    hls_playlist_type: Union[str, Literal["vod", "event"]] = "vod"
    """
    "event"
        Emit `#EXT-X-PLAYLIST-TYPE:EVENT` in the m3u8 header.
        Forces hls_list_size to 0; the playlist can only be appended to.

    "vod"
        Emit `#EXT-X-PLAYLIST-TYPE:VOD` in the m3u8 header.
        Forces hls_list_size to 0; the playlist must not change.
    """

    drop_first_segment_file: bool = True
    """Remove the first segment file.
    The first segment file will most likely contain error packets.
    """

    def get_hls_filename(self) -> str:
        return os.path.join(self.cache_dir, HLS_MASTER_FILENAME)

    def get_hls_segment_filename(self) -> str:
        return os.path.join(self.cache_dir, HLS_SEGMENT_FILENAME)

    def get_hls_options(self) -> Dict[str, Any]:
        """
        <https://ffmpeg.org/ffmpeg-formats.html#hls-2>

        :return:
            FFmpeg HLS options dictionary.
        """

        options = dict()
        options["strftime"] = "1" if self.strftime else "0"
        options["strftime_mkdir"] = "1" if self.strftime_mkdir else "0"
        options["hls_time"] = str(self.hls_time)
        if self.hls_playlist_type:
            if self.hls_playlist_type in ("vod", "event"):
                options["hls_playlist_type"] = self.hls_playlist_type
            else:
                raise ValueError(f"Unknown hls_playlist_type: {self.hls_playlist_type}")
        options["hls_segment_filename"] = self.get_hls_segment_filename()
        # "hls_list_size": "0",
        # "hls_flags": "second_level_segment_index",
        return options
