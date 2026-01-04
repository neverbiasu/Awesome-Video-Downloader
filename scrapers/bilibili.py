# -- coding: utf-8 --
import os
import re
import logging
from typing import Optional, Tuple

import requests

# Configure logging
logger = logging.getLogger(__name__)

class BiliDownloader:
    """
    Downloader for Bilibili videos.
    """
    def __init__(self):
        self.headers = {
            "Referer": "https://www.bilibili.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
            "cookies": "SESSDATA=;",
        }
        self.chunk_size = 1024 # Standardize chunk size
        self.qn = 64

    def get_url(self, url: str) -> str:
        """
        Resolve short URL (b23.tv) to original URL.
        """
        if "b23.tv" in url:
            logger.info("Resolving Bilibili share link...")

            try:
                response = requests.get(
                    url, headers=self.headers, allow_redirects=False
                )

                if response.status_code == 302:
                    original_url = response.headers.get("Location", "").split("?")[0]
                    if original_url:
                        logger.info(f"Resolved URL: {original_url}")
                        return original_url

            except Exception as e:
                logger.error(f"Failed to resolve URL: {e}")
                # Don't crash, just return original url
                pass

            return url
        else:
            logger.info(f"Original URL, no resolution needed: {url}")
            return url

    def get_bvid_and_cid(self, url: str) -> Tuple[str, int]:
        """
        Extract BVid and CID from the URL.
        """
        match = re.search(r"BV[a-zA-Z0-9]+", url)
        if not match:
             raise ValueError("Could not find BVid in URL")
        bvid = match.group(0)

        try:
            response = requests.get(
                f"https://api.bilibili.com/x/player/pagelist?bvid={bvid}",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            # Assuming the first page is the one we want
            cid = data["data"][0]["cid"]
            return bvid, cid
        except (requests.RequestException, KeyError, IndexError) as e:
            raise ValueError(f"Error fetching CID for BVID {bvid}: {e}")

    def downloader(self, url: str) -> Optional[str]:
        """
        Download video from Bilibili.
        """
        if not url:
            return None

        # Regex to find short link if embedded in text
        pattern = re.compile(r"https?://b23\.tv/[a-zA-Z0-9_/]+")
        match = pattern.search(url)
        if match:
            url = match.group(0)

        url = self.get_url(url)
        try:
            bvid, cid = self.get_bvid_and_cid(url)
        except Exception as e:
            logger.error(f"Error getting BVID/CID: {e}")
            return None

        # Request parameters
        params = {"bvid": bvid, "cid": cid, "qn": self.qn, "fnval": 16, "fnver": "0"}
        video_info_url = "https://api.bilibili.com/x/player/playurl"

        try:
            response = requests.get(video_info_url, params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            video_url = data["data"]["dash"]["video"][0]["baseUrl"]
        except Exception as e:
            logger.error(f"Error getting video URL: {e}")
            return None

        name = f"{bvid}.mp4"
        # Sanitize just in case bvid has weird chars (unlikely)
        name = re.sub(r'[\\/*?:"<>|]', "_", name)

        output_path = os.path.join(os.getcwd(), name)

        logger.info(f"Start downloading to {output_path}")
        try:
            response = requests.get(video_url, headers=self.headers, stream=True)
            response.raise_for_status()

            with open(output_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    file.write(chunk)

            logger.info(f"Download complete, saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
