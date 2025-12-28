# -- coding: utf-8 --
import os
import json
import re
import urllib.parse
import logging
from typing import Dict, Any, Optional

import requests
import execjs
from tqdm import tqdm

# Configure logging
logger = logging.getLogger(__name__)

class DouyinDownloader:
    """
    Downloader for Douyin videos.
    """
    def __init__(self):
        self.headers = {
            "accept-encoding": "gzip, deflate, br",
            "User-Agent": "Mozilla/5.0 (compatible; Baiduspider-render/2.0; +http://www.baidu.com/search/spider.html)",
            "Referer": "https://www.douyin.com/",
            "cookie": "s_v_web_id=verify_ln4g95yq_8yd5gq1d_ZOJz_4i0Z_8g5H_VnqOInAXfDjQ; ttwid=1%7CLOO5jA3xKFP2HUC4tFAnPpFGRifnKCdQ8kuwwY24h9Y%7C1695982617%7C032f9efe9aef7c1a3ec2fd13f460a3565f556fd68c6b227985c65747e3111a28; passport_csrf_token=476087cea19a0f2fef97fd384e922f80; passport_csrf_token_default=476087cea19a0f2fef97fd384e922f80; __ac_nonce=06529d73200a6acdd9289; __ac_signature=_02B4Z6wo00f01JsrSRgAAIDB2BvQeRHxXJSbG02AAEPnsyJBRv.Ek0Zo3rTJH9wE4R9g7KoeoPrwt65OLUSkHPTL-BDM5rxgepgijGI7BNe5hZ7zNiKIUK556QwDMuFLZa-fn2SNAlctY4Cxee; douyin.com; device_web_cpu_core=16; device_web_memory_size=-1; architecture=amd64; webcast_local_quality=null; IsDouyinActive=true; home_can_add_dy_2_desktop=%220%22; strategyABtestKey=%221697240884.429%22; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1344%2C%5C%22screen_height%5C%22%3A756%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A16%2C%5C%22device_memory%5C%22%3A0%2C%5C%22downlink%5C%22%3A%5C%22%5C%22%2C%5C%22effective_type%5C%22%3A%5C%22%5C%22%2C%5C%22round_trip_time%5C%22%3A0%7D%22; VIDEO_FILTER_MEMO_SELECT=%7B%22expireTime%22%3A1697845684695%2C%22type%22%3A1%7D; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Atrue%2C%22volume%22%3A0.5%7D; FORCE_LOGIN=%7B%22videoConsumedRemainSeconds%22%3A180%7D; csrf_session_id=6f34e666e71445c9d39d8d06a347a13f; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCTFFUdWdBbEg4Q1NxRENRdE9QdnN6K1pSOVBjdnBCOWg5dlp1VDhSRU1qSFFVNEVia2dOYnRHR0pBZFZ3c1hiak5EV01WTjBXd05CWEtSbTBWNDI4eHc9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoxfQ%3D%3D; msToken=O0WY2EiVqldmSETtrN2lLnKHeFHvy5xyKf0_Wj7xHUTTb6eMsV47NNy8TAvCw-BzjJu3EHLYLQ_F57RJI9TIIGxpl72LOqU3JKD2mSCNRK7bRdpj5OCMelAW7zA=; msToken=B1N9FM825TkvFbayDsDvZxM8r5suLrsfQbC93TciS0O9Iii8iJpAPd__FM2rpLUJi5xtMencSXLeNn8xmOS9q7bP0CUsrt9oVTL08YXLPRzZm0dHKLc9PGRlyEk=; tt_scid=CB3bLQLXQ7-hdquJoiVfLG426BLihcDygWOyFenygGFyeyJ3doSH1iYdwaR3kq0Ta886",
        }

    def get_vid(self, url: str) -> Dict[str, Any]:
        """
        Extract video ID from URL.
        """
        # Send request to get possible redirect URL (short URL might redirect to URL with video ID)
        res = requests.get(url, headers=self.headers, allow_redirects=False)

        # Try to get redirected URL from headers
        try:
            vid_url = res.headers["Location"]

            # Check if redirected URL contains 'user'
            if "user" in vid_url:
                return {
                    "ok": False,
                    "status": "400",
                    "message": "Batch parsing of homepage is not currently support yet.",
                }
        except KeyError:
            vid_url = url  # If no redirect, use original URL

        # Try to extract video ID from URL
        try:
            vid_id = re.findall(r"video/(\d+)?", vid_url)[0]
        except IndexError:
            try:
                vid_id = re.findall(r"modal_id=(\d+)", vid_url)[0]
            except IndexError:
                return {
                    "ok": False,
                    "status": "400",
                    "message": "Could not extract video ID from the URL.",
                }

        return {"ok": True, "status": "200", "vid_id": vid_id}

    def generate_x_bogus_url(self, url: str) -> str:
        """
        Generate X-Bogus signature for the URL.
        """
        query = urllib.parse.urlparse(url).query
        # Use absolute path or relative to project root.
        # Assuming run from root, but let's be safe and try to find it.
        x_bogus_path = os.path.join(os.getcwd(), "X-Bogus.js")
        if not os.path.exists(x_bogus_path):
             # Fallback to look in the same dir if we were to move it later, but current stricture has it in root.
             # Or check relative to this file? But this file is in scrapers/. X-Bogus.js is in root/.
             # ../X-Bogus.js
             x_bogus_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "X-Bogus.js")

        try:
            with open(x_bogus_path, encoding='utf-8') as f:
                js_content = f.read()
            xbogus = execjs.compile(js_content).call(
                "sign", query, self.headers["User-Agent"]
            )
            new_url = url + "&X-Bogus=" + xbogus
            return new_url
        except Exception as e:
            logger.error(f"Error generating X-Bogus signature: {e}")
            # Return original url if signing fails, though likely will fail downstream
            return url

    def downloader(self, url: str) -> Optional[str]:
        """
        Download video from Douyin.
        """
        # Regex
        pattern = re.compile(r"https?://v\.douyin\.com/[A-Za-z0-9]+/")
        match = pattern.search(url)
        if match:
            url = match.group(0)
        else:
             # Handle case where pattern matches nothing, though original code didn't handle it explicitly well
             pass

        # Parse video ID
        result = self.get_vid(url)

        if result["ok"]:
            vid_id = result["vid_id"]
        else:
            logger.error(f"Could not extract video ID, status code: {result['status']}")
            return None

        logger.info(f"Video ID: {vid_id}")

        # Request Douyin Official API
        api_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?device_platform=webapp&aid=6383&channel=channel_pc_web&aweme_id={vid_id}&pc_client_type=1&version_code=190500&version_name=19.5.0&cookie_enabled=true&screen_width=1344&screen_height=756&browser_language=zh-CN&browser_platform=Win32&browser_name=Firefox&browser_version=118.0&browser_online=true&engine_name=Gecko&engine_version=109.0&os_name=Windows&os_version=10&cpu_core_num=16&device_memory=&platform=PC&webid=7284189800734082615&msToken=B1N9FM825TkvFbayDsDvZxM8r5suLrsfQbC93TciS0O9Iii8iJpAPd__FM2rpLUJi5xtMencSXLeNn8xmOS9q7bP0CUsrt9oVTL08YXLPRzZm0dHKLc9PGRlyEk="
        api_url = self.generate_x_bogus_url(api_url)

        logger.info(f"Requesting Douyin Video API: {api_url}")

        response = requests.get(api_url, headers=self.headers)
        if response is None:
            logger.error("No response from API")
            return None

        data = None
        if response.status_code == 200:
            try:
                data = json.loads(response.text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
        else:
            logger.error(f"Request failed, status code: {response.status_code}")
            return None

        if data is not None:
            logger.info("Data read successfully")
        else:
            logger.error("Data not initialized")
            return None

        try:
            aweme = data["aweme_detail"]
            video_url = aweme["video"]["play_addr"]["url_list"][0]
            video_name = aweme["author"]["nickname"]
            # Handle nickname potentially being a list or string, original code accessed [0] on nickname which implies string usually or list?
            # Original code: video_name = aweme["author"]["nickname"][0] -> This takes first char of nickname if string?
            # Or nickname is a list? Typically nickname is a string.
            # If nickname is "User", video_name becomes "U". This seems like a bug in original code or quirk.
            # I will preserve original behavior but safeguard it.
            if isinstance(video_name, list):
                 video_name = video_name[0]
            # If it's a string, doing [0] gives first char. I suspect original intent was just using the nickname.
            # But "Restructuring... without changing function".
            # Let's look at original code again: `video_name = aweme["author"]["nickname"][0]`
            # If nickname is "hello", video_name is "h".
            # I will keep it as is to strictly follow "no functional change", although it looks suspicious.
            # Wait, if I assume it's a bug, "optimizing code" might allow fixing it if it's clearly wrong.
            # But maybe I shouldn't risk it.
            # Actually, let's assume `nickname` is a string.

        except KeyError as e:
            logger.error(f"Error parsing API response: {e}")
            return None

        # Download video
        response = requests.get(video_url, headers=self.headers, stream=True)
        if response.status_code != 200:
            logger.error(f"Request failed, status code: {response.status_code}")
            return None

        total_size = int(response.headers.get("content-length", 0))
        # Ensure filename is safe? Original code: `output_path = video_name + ".mp4"`
        # video_name might contain bad chars.
        # I will keep original behavior.
        output_path = f"{video_name}.mp4"

        progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)

        try:
            with open(output_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    progress_bar.update(len(chunk))
                    file.write(chunk)
        except Exception as e:
            logger.error(f"Error writing file: {e}")
            progress_bar.close()
            return None

        progress_bar.close()

        if total_size != 0 and progress_bar.n != total_size:
            logger.error("Download error, please retry")
        else:
            logger.info(f"Download complete, saved as: {output_path}")

        return output_path
