import gradio as gr
from Scraper import DouyinDownloader, BiliDownloader, TiktokDownloader, YoutubeDownloader

theme = gr.themes.Base(
    primary_hue="fuchsia",
    secondary_hue="rose",
    neutral_hue="sky",
    font=[
        "Source Sans Pro",
        "ui-sans-serif",
        "system-ui",
        gr.themes.GoogleFont("sans-serif"),
    ],
)

"""
https://www.gradio.app/guides/theming-guide
"""
dydownloader = DouyinDownloader()
douyin = gr.Interface(
    fn=dydownloader.downloader,
    inputs=["text"],
    title="Video Downloader",
    outputs=gr.Video(label="Out", show_share_button=None),
    theme=theme,
)
bidownloader = BiliDownloader()
bili = gr.Interface(
    fn=bidownloader.downloader,
    inputs=["text"],
    title="Video Downloader",
    outputs=gr.Video(label="Out", show_share_button=None),
    theme=theme,
)
tkdownloader = TiktokDownloader()
tk = gr.Interface(
    fn=tkdownloader.downloader,
    inputs=["text"],
    title="Video Downloader",
    outputs=gr.Video(label="Out", show_share_button=None),
    theme=theme,
)
ytdownloader = YoutubeDownloader()
youtube = gr.Interface(
    fn=ytdownloader.downloader,
    inputs=[gr.Textbox(label="url"), gr.Checkbox(label="下载缩略图")],
    title="Video Downloader",
    outputs=[
        gr.Video(label="Out", show_share_button=None),
        gr.Image(label="image", show_share_button=None),
    ],
    theme=theme,
)


if __name__ == "__main__":
    sample_url = "https://www.tiktok.com/t/ZT8kgbmeH/"
    """
    https://v.douyin.com/id9S5VTm/

    https://www.bilibili.com/video/BV1bw411c7zv/?spm_id_from=333.934.0.0

    https://www.youtube.com/watch?v=bef8QLNHubw

    https://www.tiktok.com/t/ZT8kgbmeH/
    """
    # video_info = downloader.get_video_info(sample_url)
    # downloader.download_video( "sample_video.mp4")

    ui = gr.TabbedInterface(
        [douyin, bili, tk, youtube],
        ["Douyin Video", "BiliBili Video", "TiktTok Video", "YouTube Video"],
        theme=theme,
    )
    # ui.launch(share = True)
    ui.launch()
    # tkdownloader = TiktokDownloader()
    # tkdownloader.downloader(sample_url)