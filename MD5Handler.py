import hashlib
import html
from html.parser import HTMLParser


class HTMLTagStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_clean_text(self):
        return ''.join(self.text)


def clean_html(raw: str) -> str:
    if not raw:
        return ""

    # 去除HTML标签
    stripper = HTMLTagStripper()
    stripper.feed(raw)
    clean = stripper.get_clean_text()

    # 转换HTML实体 &amp; -> & 等
    return html.unescape(clean)


def generate_md5(author: str, artist: str, song: str, strip_html=True) -> str:
    # 处理空值
    author = author or ""
    artist = artist or ""
    song = song or ""

    # 可选清理HTML
    if strip_html:
        author = clean_html(author)
        artist = clean_html(artist)
        song = clean_html(song)

    # 拼接计算
    combined = f"{author}{artist}{song}"
    return hashlib.md5(combined.encode('utf-8')).hexdigest()
