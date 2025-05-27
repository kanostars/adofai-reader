import hashlib

def generate_md5(author: str, artist: str, song: str) -> str:
    # 处理空值
    author = author or ""
    artist = artist or ""
    song = song or ""

    # 拼接计算
    combined = f"{author}{artist}{song}"
    return hashlib.md5(combined.encode('utf-8')).hexdigest()
