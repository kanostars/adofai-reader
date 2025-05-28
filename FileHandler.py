import json
import logging
import re
import winreg
import os


def open_adofai(workshop_id: str):
    url = os.path.join(base_url, workshop_id, 'main.adofai')
    try:
        with open(url, 'r', newline='\r', encoding='utf-8-sig', errors='ignore') as f:
            text = f.read()
            text = text.replace(r'\n', '\n')
        author = re.search(r'"author":\s*"((?:\\"|.)*?)"', text, flags=re.DOTALL)
        artist = re.search(r'"artist":\s*"((?:\\"|.)*?)"', text, flags=re.DOTALL)
        song = re.search(r'"song":\s*"((?:\\"|.)*?)"', text, flags=re.DOTALL)
        # print('author: ', author.group(1), 'artist: ', artist.group(1), 'song: ', song.group(1))
        # print()
        return author.group(1).replace('\\"', '"'), artist.group(1).replace('\\"', '"'), song.group(1).replace('\\"', '"')
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

def load_md5_cache():
    """加载MD5缓存"""
    try:
        with open(md5_cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(md5_cache_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        return {}

def save_md5_cache(md5_cache):
    """保存MD5缓存"""
    with open(md5_cache_path, 'w', encoding='utf-8') as f:
        json.dump(md5_cache, f, ensure_ascii=False, indent=4)

def load_status_data():
    """加载按钮保存状态数据"""
    if os.path.exists(status_file_path):
        with open(status_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'data': [True, True, True, True]}

def save_status_data(status_data):
    """保存按钮状态数据"""
    with open(status_file_path, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, ensure_ascii=False, indent=4)

def load_song_data():
    """加载歌曲基本信息"""
    try:
        with open(data_file_path, 'r', encoding='utf-8') as f:
            raw_songs = json.load(f)
            return [song for song in raw_songs if isinstance(song, dict)]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def load_custom_data():
    """加载存档数据"""
    with open(custom_data_path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

base_url = os.path.join(get_steam_install_path(), 'steamapps', 'workshop', 'content', '977950')
custom_data_path = os.path.join(get_steam_install_path(), 'steamapps', 'common', 'A Dance of Fire and Ice', 'User', 'custom_data.sav')
md5_cache_path = 'resource/workshop_md5_map.json'
data_file_path = 'resource/levels_info.json'
status_file_path = 'resource/status.json'
