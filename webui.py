import logging
import gradio as gr
from scrapers import DouyinDownloader, BiliDownloader, TiktokDownloader, YoutubeDownloader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Theme configuration
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

def create_interface() -> gr.TabbedInterface:
    """
    Creates and configures the Gradio interface.
    """
    dydownloader = DouyinDownloader()
    douyin = gr.Interface(
        fn=dydownloader.downloader,
        inputs=[gr.Textbox(label="URL", placeholder="https://v.douyin.com/...")],
        title="Douyin Downloader",
        outputs=gr.Video(label="Output Video", show_share_button=False),
        theme=theme,
        allow_flagging="never"
    )

    bidownloader = BiliDownloader()
    bili = gr.Interface(
        fn=bidownloader.downloader,
        inputs=[gr.Textbox(label="URL", placeholder="https://www.bilibili.com/video/BV...")],
        title="Bilibili Downloader",
        outputs=gr.Video(label="Output Video", show_share_button=False),
        theme=theme,
        allow_flagging="never"
    )

    tkdownloader = TiktokDownloader()
    tk = gr.Interface(
        fn=tkdownloader.downloader,
        inputs=[gr.Textbox(label="URL", placeholder="https://www.tiktok.com/t/...")],
        title="TikTok Downloader",
        outputs=gr.Video(label="Output Video", show_share_button=False),
        theme=theme,
        allow_flagging="never"
    )

    ytdownloader = YoutubeDownloader()
    youtube = gr.Interface(
        fn=ytdownloader.downloader,
        inputs=[
            gr.Textbox(label="URL", placeholder="https://www.youtube.com/watch?v=..."),
            gr.Checkbox(label="Download Thumbnail")
        ],
        title="YouTube Downloader",
        outputs=[
            gr.Video(label="Output Video", show_share_button=False),
            gr.Image(label="Thumbnail", show_share_button=False),
        ],
        theme=theme,
        allow_flagging="never"
    )

    ui = gr.TabbedInterface(
        [douyin, bili, tk, youtube],
        ["Douyin", "BiliBili", "TikTok", "YouTube"],
        theme=theme,
        title="Video Downloader"
    )
    return ui

if __name__ == "__main__":
    ui = create_interface()
    ui.queue().launch()
