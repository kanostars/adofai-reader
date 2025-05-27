import logging
import winreg

import json5
import os


def openAdofai(url: str):
    url = os.path.join(base_url, url.split('=')[-1], 'main.adofai')
    try:
        with open(url, 'r', encoding='utf-8-sig', errors='ignore') as f:
            data = json5.load(f)
        author = data['settings']['author']
        artist = data['settings']['artist']
        song = data['settings']['song']
        return author, artist, song
    except FileNotFoundError:
        logging.info(f"File not found: {url}")
        return None, None, None
    except ValueError:
        logging.error(f"Invalid JSON: {url}")
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
