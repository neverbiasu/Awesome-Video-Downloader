# -- coding: utf-8 --
import os
import re
import logging
from typing import Optional, Tuple, Union

import requests
from pytube import YouTube

# Configure logging
logger = logging.getLogger(__name__)

class YoutubeDownloader:
    """
    Downloader for YouTube videos.
    """
    def __init__(self):
        self.use_oauth = (False,)
        self.allow_oauth_cache = True

    def sanitize_filename(self, filename: str) -> str:
        """
        Replace disallowed characters in filename with underscores.
        """
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def downloader(self, url: str, output_thumbnail: bool = False) -> Union[Tuple[str, Optional[str]], Tuple[str, None]]:
        """
        Download video from YouTube.
        """
        yt = YouTube(
            url,
            proxies="",
            # use_oauth=self.use_oauth,
            # allow_oauth_cache=self.allow_oauth_cache
        )
        yt.streams.filter(file_extension="mp4")

        thumbnail_output = None
        if output_thumbnail:
            thumbnail_url = yt.thumbnail_url
            try:
                thumbnail_data = requests.get(thumbnail_url).content
                thumbnail_filename = f"{self.sanitize_filename(yt.title)}.jpg"
                with open(thumbnail_filename, "wb") as f:
                    f.write(thumbnail_data)
                thumbnail_output = os.path.join(os.getcwd(), thumbnail_filename)
            except Exception as e:
                logger.error(f"Error downloading thumbnail: {e}")

        logger.info(f"Start downloading: {yt.title}")
        if yt.title is None:
            logger.warning("Title is None")
        else:
            pass # logger.info(yt.title) already logged above

        try:
            filename = f"{yt.title}.mp4"
        except Exception:
            filename = "None.mp4"

        filename = self.sanitize_filename(filename)
        logger.debug(f"Filename: {filename}")

        try:
            stream = yt.streams.get_by_itag(22)
            if stream is None:
                 # Fallback if 720p (itag 22) is not available
                 stream = yt.streams.get_highest_resolution()

            video_output = os.path.join(os.getcwd(), filename)
            stream.download(output_path="", filename=filename) # Explicit filename to match our logic

            # Original code logic for filename extension:
            # file_type = "." + stream.mime_type.split("/")[1]
            # filename = stream.default_filename if filename is None else filename + file_type
            # But stream.download handles extension if not provided, or we force it.

            logger.info(f"Download successful! Saved to: {video_output}")

            if output_thumbnail:
                return video_output, thumbnail_output
            else:
                return video_output, None

        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            # Depending on how the caller expects, we might raise or return paths that don't exist?
            # Existing code returned paths even if download might have failed (though it crashed on error).
            # I will re-raise or return None? The signature implies returning paths.
            # I'll let the exception propagate or return partial?
            # Original code crashed on error. I will catch and re-raise to be safe or just log.
            raise e
