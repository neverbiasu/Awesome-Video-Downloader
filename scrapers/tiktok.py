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
                response = requests.get(
                    url,
                    headers=self.headers,
                    proxies="",
                    allow_redirects=False,
                    timeout=10,
                )
                if response.status_code == 301:
                    location = response.headers["Location"]
                    url = location.split("?")[0] if "?" in location else location
                    logger.info(f"Resolved URL: {url}")
                    return url
            except Exception as e:
                logger.error("Failed to resolve URL!")
                logger.error(e)
                return None
        return url # Return potentially unresolved url if no 301?

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
                 # Should probably return None if not found
                 logger.warning("Could not find video ID pattern in URL")
                 return None

            return video_id
        except Exception as e:
            logger.error(f"Error getting TikTok video ID: {e}")
            return None

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
                api_url, headers=self.headers, proxies="", timeout=10
            )
            response.raise_for_status()

            # The original code parsed JSON directly from response.text
            data = response.json()

            # Original code logic:
            # video_url = response.json()["aweme_list"][0] # This looks wrong in original, overwritten immediately
            # video_url = data["aweme_list"][0]["video"]["play_addr"]["url_list"][0]

            aweme_list = data.get("aweme_list", [])
            if not aweme_list:
                logger.error("No aweme_list found in response")
                return None

            video_url = aweme_list[0]["video"]["play_addr"]["url_list"][0]

            # Download video
            response = requests.get(video_url, headers=self.headers, stream=True)
            if response.status_code != 200:
                logger.error(f"Request failed, status code: {response.status_code}")
                return None

            desc = aweme_list[0]["desc"]
            # Use regex to find words not containing #
            result = re.findall(r"\b(?!#)\w+\b", desc)

            # Join results to generate filename
            name = " ".join(result)
            output_path = name + ".mp4"

            total_size = int(response.headers.get("content-length", 0))
            progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)

            with open(output_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    progress_bar.update(len(chunk))
                    file.write(chunk)

            progress_bar.close()
            return output_path

        except Exception as e:
            logger.error(f"Failed to get video info or download: {e}")
            raise e
