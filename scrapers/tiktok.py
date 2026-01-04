# -- coding: utf-8 --
import json
import re
import logging
from typing import Optional

import requests
from tqdm import tqdm

# Configure logging
logger = logging.getLogger(__name__)

API_URL_TEMPLATE = "https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aweme_id={vid}"

class TiktokDownloader:
    """
    Downloader for TikTok videos.
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "com.ss.android.ugc.trill/494+Mozilla/5.0+(Linux;+Android+12;+2112123G+Build/SKQ1.211006.001;+wv)+AppleWebKit/537.36+(KHTML,+like+Gecko)+Version/4.0+Chrome/107.0.5304.105+Mobile+Safari/537.36"
        }

    def get_url(self, url: str) -> Optional[str]:
        """
        Resolve share URL to original URL.
        """
        if "@" in url:
            logger.info(f"Original URL, no resolution needed: {url}")
            return url
        else:
            logger.info("Resolving TikTok share link...")
            try:
                # proxies="" causes issues in some environments if no proxy is needed, better to just omit it or use None
                response = requests.get(
                    url,
                    headers=self.headers,
                    allow_redirects=False,
                    timeout=10,
                )
                if response.status_code == 301:
                    location = response.headers["Location"]
                    url = location.split("?")[0] if "?" in location else location
                    logger.info(f"Resolved URL: {url}")
                    return url
            except Exception as e:
                logger.error(f"Failed to resolve URL: {e}")
                # Don't return None immediately, try to proceed with original URL might be safer?
                # Or if resolution failed, maybe it's invalid. Original code returned None.
                return None
        return url

    def get_vid(self, url: str) -> Optional[str]:
        """
        Extract video ID from URL.
        """
        try:
            # Resolve URL
            url = self.get_url(url)
            if not url:
                return None

            # Extract video ID
            if "/video/" in url:
                video_id = re.findall(r"/video/(\d+)", url)[0]
            elif "/v/" in url:
                video_id = re.findall(r"/v/(\d+)", url)[0]
            else:
                 logger.warning("Could not find video ID pattern in URL")
                 return None

            return video_id
        except Exception as e:
            logger.error(f"Error getting TikTok video ID: {e}")
            return None

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to remove illegal characters.
        """
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def downloader(self, url: str) -> Optional[str]:
        """
        Download video from TikTok.
        """
        vid = self.get_vid(url)
        if not vid:
            logger.error("Could not obtain video ID")
            return None

        api_url = API_URL_TEMPLATE.format(vid=vid)
        try:
            logger.info(f"Getting video data API: {api_url}")
            response = requests.get(
                api_url, headers=self.headers, timeout=10
            )
            response.raise_for_status()

            data = response.json()

            aweme_list = data.get("aweme_list", [])
            if not aweme_list:
                logger.error("No aweme_list found in response")
                return None

            video_url = aweme_list[0]["video"]["play_addr"]["url_list"][0]

            desc = aweme_list[0]["desc"]
            # Use regex to find words not containing #
            result = re.findall(r"\b(?!#)\w+\b", desc)

            # Join results to generate filename
            name = " ".join(result)
            if not name:
                name = f"tiktok_{vid}"

            name = self.sanitize_filename(name)
            output_path = f"{name}.mp4"

            # Download video
            logger.info(f"Downloading video to {output_path}")
            response = requests.get(video_url, headers=self.headers, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)

            with open(output_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    progress_bar.update(len(chunk))
                    file.write(chunk)

            progress_bar.close()

            if total_size != 0 and progress_bar.n != total_size:
                logger.error("Download incomplete")
                return None

            return output_path

        except Exception as e:
            logger.error(f"Failed to get video info or download: {e}")
            return None
