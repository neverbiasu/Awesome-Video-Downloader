# -- coding: utf-8 --**
import requests
import json
import re
from tqdm import tqdm
import urllib
import urllib.parse
import execjs
import json
from moviepy.editor import *
import os
from pytube import YouTube
from pytube.helpers import safe_filename


class DouyinDownloader:
    def __init__(self):
        self.headers = {
            "accept-encoding": "gzip, deflate, br",
            "User-Agent": "Mozilla/5.0 (compatible; Baiduspider-render/2.0; +http://www.baidu.com/search/spider.html)",
            "Referer": "https://www.douyin.com/",
            "cookie": "s_v_web_id=verify_ln4g95yq_8yd5gq1d_ZOJz_4i0Z_8g5H_VnqOInAXfDjQ; ttwid=1%7CLOO5jA3xKFP2HUC4tFAnPpFGRifnKCdQ8kuwwY24h9Y%7C1695982617%7C032f9efe9aef7c1a3ec2fd13f460a3565f556fd68c6b227985c65747e3111a28; passport_csrf_token=476087cea19a0f2fef97fd384e922f80; passport_csrf_token_default=476087cea19a0f2fef97fd384e922f80; __ac_nonce=06529d73200a6acdd9289; __ac_signature=_02B4Z6wo00f01JsrSRgAAIDB2BvQeRHxXJSbG02AAEPnsyJBRv.Ek0Zo3rTJH9wE4R9g7KoeoPrwt65OLUSkHPTL-BDM5rxgepgijGI7BNe5hZ7zNiKIUK556QwDMuFLZa-fn2SNAlctY4Cxee; douyin.com; device_web_cpu_core=16; device_web_memory_size=-1; architecture=amd64; webcast_local_quality=null; IsDouyinActive=true; home_can_add_dy_2_desktop=%220%22; strategyABtestKey=%221697240884.429%22; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1344%2C%5C%22screen_height%5C%22%3A756%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A16%2C%5C%22device_memory%5C%22%3A0%2C%5C%22downlink%5C%22%3A%5C%22%5C%22%2C%5C%22effective_type%5C%22%3A%5C%22%5C%22%2C%5C%22round_trip_time%5C%22%3A0%7D%22; VIDEO_FILTER_MEMO_SELECT=%7B%22expireTime%22%3A1697845684695%2C%22type%22%3A1%7D; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Atrue%2C%22volume%22%3A0.5%7D; FORCE_LOGIN=%7B%22videoConsumedRemainSeconds%22%3A180%7D; csrf_session_id=6f34e666e71445c9d39d8d06a347a13f; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCTFFUdWdBbEg4Q1NxRENRdE9QdnN6K1pSOVBjdnBCOWg5dlp1VDhSRU1qSFFVNEVia2dOYnRHR0pBZFZ3c1hiak5EV01WTjBXd05CWEtSbTBWNDI4eHc9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoxfQ%3D%3D; msToken=O0WY2EiVqldmSETtrN2lLnKHeFHvy5xyKf0_Wj7xHUTTb6eMsV47NNy8TAvCw-BzjJu3EHLYLQ_F57RJI9TIIGxpl72LOqU3JKD2mSCNRK7bRdpj5OCMelAW7zA=; msToken=B1N9FM825TkvFbayDsDvZxM8r5suLrsfQbC93TciS0O9Iii8iJpAPd__FM2rpLUJi5xtMencSXLeNn8xmOS9q7bP0CUsrt9oVTL08YXLPRzZm0dHKLc9PGRlyEk=; tt_scid=CB3bLQLXQ7-hdquJoiVfLG426BLihcDygWOyFenygGFyeyJ3doSH1iYdwaR3kq0Ta886",
        }

    def get_vid(self, url):
        # 发送请求以获取可能的重定向URL（短URL可能会重定向到带有视频ID的URL）
        res = requests.get(url, headers=self.headers, allow_redirects=False)

        # 尝试从响应头中获取重定向的URL
        try:
            vid_url = res.headers["Location"]

            # 检查重定向的URL是否包含'user'
            if "user" in vid_url:
                return {
                    "ok": False,
                    "status": "400",
                    "message": "Batch parsing of homepage is not currently support yet.",
                }
        except KeyError:
            vid_url = url  # 如果没有重定向，则使用原始URL

        # 尝试从URL中提取视频ID
        try:
            vid_id = re.findall("video/(\d+)?", vid_url)[0]
        except IndexError:
            try:
                vid_id = re.findall("modal_id=(\d+)", vid_url)[0]
            except IndexError:
                return {
                    "ok": False,
                    "status": "400",
                    "message": "Could not extract video ID from the URL.",
                }

        return {"ok": True, "status": "200", "vid_id": vid_id}

    # 生成X-Bogus签名/Generate X-Bogus signature
    def generate_x_bogus_url(self, url):
        query = urllib.parse.urlparse(url).query
        xbogus = execjs.compile(open("./X-Bogus.js").read()).call(
            "sign", query, self.headers["User-Agent"]
        )
        new_url = url + "&X-Bogus=" + xbogus
        return new_url

    def downloader(self, url):
        # 正则
        pattern = re.compile(r"https?://v\.douyin\.com/[A-Za-z0-9]+/")
        match = pattern.search(url)
        url = match.group(0)

        # 解析视频ID
        result = self.get_vid(url)

        if result["ok"]:  # 检查是否成功提取了视频ID
            vid_id = result["vid_id"]
        else:
            print(f"无法提取视频ID, 状态码：{result['status']}")

        print(vid_id)
        # 请求抖音官方API
        api_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?device_platform=webapp&aid=6383&channel=channel_pc_web&aweme_id={vid_id}&pc_client_type=1&version_code=190500&version_name=19.5.0&cookie_enabled=true&screen_width=1344&screen_height=756&browser_language=zh-CN&browser_platform=Win32&browser_name=Firefox&browser_version=118.0&browser_online=true&engine_name=Gecko&engine_version=109.0&os_name=Windows&os_version=10&cpu_core_num=16&device_memory=&platform=PC&webid=7284189800734082615&msToken=B1N9FM825TkvFbayDsDvZxM8r5suLrsfQbC93TciS0O9Iii8iJpAPd__FM2rpLUJi5xtMencSXLeNn8xmOS9q7bP0CUsrt9oVTL08YXLPRzZm0dHKLc9PGRlyEk="
        api_url = self.generate_x_bogus_url(api_url)
        # 访问API/Access API
        print("正在请求抖音视频API: {}".format(api_url))
        # 发送请求
        response = requests.get(api_url, headers=self.headers)
        if response is None:
            print("No response")
        # else:
        # print(response)
        # print(response.text)
        data = None  # 初始化变量
        if response.status_code == 200:
            try:
                data = json.loads(response.text)
            except json.JSONDecodeError as e:
                print(f"JSON 解码错误: {e}")
        else:
            print(f"请求失败，状态码： {response.status_code}")
        # 处理请求
        # print(response.text)
        if data is not None:
            print("数据读取成功")
        else:
            print("数据未初始化")
        aweme = data["aweme_detail"]
        # print(aweme)
        video_url = aweme["video"]["play_addr"]["url_list"][0]  # 根据最新API文档更新
        video_name = aweme["author"]["nickname"][0]
        # 下载视频
        response = requests.get(video_url, headers=self.headers, stream=True)
        if response.status_code != 200:
            print(f"请求失败，状态码： {response.status_code}")
            return

        total_size = int(response.headers.get("content-length", 0))
        progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)

        output_path = video_name + ".mp4"
        with open(output_path, "wb") as file:
            for data in response.iter_content(chunk_size=1024):
                progress_bar.update(len(data))
                file.write(data)

        progress_bar.close()

        if total_size != 0 and progress_bar.n != total_size:
            print("下载出错，请重试")
        else:
            print(f"下载完成，文件已保存为: {output_path}")
        return output_path


class BiliDownloader:
    def __init__(self):
        self.headers = {
            "Referer": "https://www.bilibili.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
            "cookies": "SESSDATA=;",
        }
        self.chunk_size = 720
        self.qn = 64

    def get_url(self, url):
        if "b23.tv" in url:
            print("正在通过哔哩哔哩分享链接获取原始链接...")

            try:
                response = requests.get(
                    url, headers=self.headers, allow_redirects=False
                )

                if response.status_code == 302:
                    original_url = response.headers["Location"].split("?")[0]
                    print("获取原始链接成功, 原始链接为: {}".format(original_url))
                    return original_url

            except Exception as e:
                print("获取原始链接失败!")
                print(e)
                raise e

        else:
            print("该链接为原始链接,无需转换,原始链接为: {}".format(url))
            return url

    def get_bvid_and_cid(self, url):
        bvid = re.search(r"BV[a-zA-Z0-9]+", url).group(0)
        response = requests.get(
            f"https://api.bilibili.com/x/player/pagelist?bvid={bvid}",
            headers=self.headers,
        )
        cid = response.json()["data"][0]["cid"]
        return bvid, cid

    def downloader(self, url):
        # 【Git + GitHub 10分钟完全入门 (进阶)-哔哩哔哩】 https://b23.tv/oOUPZEM
        # 正则
        pattern = re.compile(r"https?://b23\.tv/[a-zA-Z0-9_/]+")
        match = pattern.search(url)
        url = match.group(0)
        url = self.get_url(url)
        bvid, cid = self.get_bvid_and_cid(url)
        # 请求参数
        params = {"bvid": bvid, "cid": cid, "qn": 64, "fnval": 16, "fnver": "0"}
        video_url = f"https://api.bilibili.com/x/player/playurl"
        response = requests.get(video_url, params, headers=self.headers)
        video_url = response.json()["data"]["dash"]["video"][0]["baseUrl"]
        name = f"{bvid}.mp4"
        output_path = os.path.join(os.getcwd(), name)

        print("开始下载")
        response = requests.get(video_url, headers=self.headers, stream=True)
        print(response)
        if response.status_code == 200:
            with open(output_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    file.write(chunk)
            print(f"下载完成，文件保存在 {output_path}")
            return output_path
        else:
            print(f"{name} 下载失败")
            return None


class YoutubeDownloader:
    def __init__(self):
        self.use_oauth = (False,)
        self.allow_oauth_cache = True

    def sanitize_filename(self, filename):
        # 替换不允许的文件名字符为下划线
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def downloader(self, url, output_thumbnail=False):
        yt = YouTube(
            url,
            # on_progress_callback=progress_func,
            # on_complete_callback=complete_func,
            proxies="",
            # use_oauth=self.use_oauth,
            # allow_oauth_cache=self.allow_oauth_cache
        )
        yt.streams.filter(file_extension="mp4")

        if output_thumbnail:
            thumbnail_url = yt.thumbnail_url
            thumbnail_data = requests.get(thumbnail_url).content
            thumbnail_filename = f"{self.sanitize_filename(yt.title)}.jpg"
            with open(thumbnail_filename, "wb") as f:
                f.write(thumbnail_data)
            thumbnail_output = os.path.join(os.getcwd(), thumbnail_filename)

        print("开始下载: %s" % yt.title)
        if yt.title is None:
            print("啥也没有")
        else:
            print(yt.title)
        try:
            filename = f"{yt.title}.mp4"
        except Exception:
            filename = "None.mp4"
        print(filename)
        filename = self.sanitize_filename(filename)
        print(filename)
        """if filename:
            filename = safe_filename(filename)"""
        stream = yt.streams.get_by_itag(22)
        video_output = os.path.join(os.getcwd(), filename)
        stream.download(output_path="")
        file_type = "." + stream.mime_type.split("/")[1]
        # filename = stream.default_filename if filename is None else filename + file_type
        print("下载成功! 文件保存在: %s" % video_output)

        if output_thumbnail:
            return video_output, thumbnail_output  # 返回视频和缩略图
        else:
            return video_output, None  # 只返回视频


class TiktokDownloader:
    def __init__(self):
        self.headers = {
            "User-Agent": "com.ss.android.ugc.trill/494+Mozilla/5.0+(Linux;+Android+12;+2112123G+Build/SKQ1.211006.001;+wv)+AppleWebKit/537.36+(KHTML,+like+Gecko)+Version/4.0+Chrome/107.0.5304.105+Mobile+Safari/537.36"
        }

    def get_url(self, url):
        if "@" in url:
            print(f"该链接为原始链接,无需转换,原始链接为: {url}")
            return url
        else:
            print("正在通过TikTok分享链接获取原始链接...")
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
                    print(f"获取原始链接成功, 原始链接为: {url}")
                    return url
            except Exception as e:
                print("获取原始链接失败！")
                print(e)
                return None

    def get_vid(self, url):
        try:
            # 转换链接
            url = self.get_url(url)
            # 获取视频ID
            if "/video/" in url:
                video_id = re.findall("/video/(\d+)", url)[0]
            elif "/v/" in url:
                video_id = re.findall("/v/(\d+)", url)[0]
            # print('获取到的TikTok视频ID是{}'.format(video_id))
            # 返回视频ID
            return video_id
        except Exception as e:
            print(f"获取TikTok视频ID出错了: {e}")
            return None

    def downloader(self, url):
        vid = self.get_vid(url)
        api_url = (
            f"https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aweme_id={vid}"
        )
        try:
            print(f"正在获取视频数据API: {api_url}")
            response = requests.get(
                api_url, headers=self.headers, proxies="", timeout=10
            )
            response.raise_for_status()  # 检查请求是否成功
            video_url = response.json()["aweme_list"][0]
            # print(response.text)
            """with open("response.txt", "w", encoding="utf-8") as file:
                file.write(response.text)"""
            data = json.loads(response.text)
            video_url = data["aweme_list"][0]["video"]["play_addr"]["url_list"][0]
            response = requests.get(video_url, headers=self.headers, stream=True)
            if response.status_code != 200:
                print(f"请求失败，状态码： {response.status_code}")
                return
            desc = data["aweme_list"][0]["desc"]
            # 使用正则表达式找出不包含#的单词
            result = re.findall(r"\b(?!#)\w+\b", desc)

            # 连接结果生成一个新的字符串
            name = " ".join(result)
            output_path = name + ".mp4"
            total_size = int(response.headers.get("content-length", 0))
            progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)
            with open(output_path, "wb") as file:
                for data in response.iter_content(chunk_size=1024):
                    progress_bar.update(len(data))
                    file.write(data)

            return output_path
        except Exception as e:
            print(f"获取视频信息失败！原因: {e}")
            raise e
