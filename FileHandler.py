import logging
import re
import winreg

import os


def openAdofai(url: str):
    url = os.path.join(base_url, url.split('&')[0].split('=')[-1], 'main.adofai')
    try:
        with open(url, 'r', newline='\r', encoding='utf-8-sig', errors='ignore') as f:
            text = f.read()
            text = text.replace(r'\n', '\n')
        author = re.search(r'"author":\s*"([^"]+)"', text)
        artist = re.search(r'"artist":\s*"([^"]+)"', text)
        song = re.search(r'"song":\s*"([^"]+)"', text)
        # print('author: ', author.group(1), 'artist: ', artist.group(1), 'song: ', song.group(1).encode())
        # print()
        return author.group(1), artist.group(1), song.group(1)
    except FileNotFoundError:
        logging.info(f"File not found: {url}")
        return None, None, None
    except Exception as e:
        logging.error(e)
        return None, None, None


def get_steam_install_path():
    try:
        # 尝试访问 64 位系统的注册表路径
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Valve\Steam",
            0,  # 默认访问权限
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )
    except FileNotFoundError:
        try:
            # 如果找不到，尝试 32 位路径
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Valve\Steam",
                0,
                winreg.KEY_READ
            )
        except FileNotFoundError:
            return None

    try:
        # 读取 InstallPath 的值
        value, _ = winreg.QueryValueEx(key, "InstallPath")
        return value
    except FileNotFoundError:
        return None
    finally:
        winreg.CloseKey(key)


base_url = os.path.join(get_steam_install_path(), 'steamapps', 'workshop', 'content', '977950')
