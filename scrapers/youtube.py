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
        self.use_oauth = False
        self.allow_oauth_cache = True

    def sanitize_filename(self, filename: str) -> str:
        """
        Replace disallowed characters in filename with underscores.
        """
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def downloader(self, url: str, output_thumbnail: bool = False) -> Tuple[Optional[str], Optional[str]]:
        """
        Download video from YouTube.
        """
        try:
            # proxies="" can be problematic, better to rely on env vars or None
            yt = YouTube(url)
        except Exception as e:
            logger.error(f"Error initializing YouTube object: {e}")
            return None, None

        thumbnail_output = None
        if output_thumbnail:
            try:
                thumbnail_url = yt.thumbnail_url
                thumbnail_data = requests.get(thumbnail_url).content
                thumbnail_filename = f"{self.sanitize_filename(yt.title)}.jpg"
                with open(thumbnail_filename, "wb") as f:
                    f.write(thumbnail_data)
                thumbnail_output = os.path.join(os.getcwd(), thumbnail_filename)
            except Exception as e:
                logger.error(f"Error downloading thumbnail: {e}")

        logger.info(f"Start downloading: {yt.title}")

        filename = f"{yt.title}.mp4" if yt.title else "youtube_video.mp4"
        filename = self.sanitize_filename(filename)
        logger.debug(f"Filename: {filename}")

        try:
            stream = yt.streams.filter(file_extension="mp4", progressive=True).get_highest_resolution()
            if stream is None:
                 logger.warning("No progressive MP4 stream found, trying any stream")
                 stream = yt.streams.get_highest_resolution()

            if stream:
                video_output = os.path.join(os.getcwd(), filename)
                stream.download(output_path=os.getcwd(), filename=filename)
                logger.info(f"Download successful! Saved to: {video_output}")
                return video_output, thumbnail_output
            else:
                logger.error("No suitable stream found")
                return None, thumbnail_output

        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None, thumbnail_output
