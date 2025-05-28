import logging
import os.path
import sys
import json

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QGroupBox,
    QScrollArea, QSizePolicy, QSpacerItem, QComboBox
)
from PyQt6.QtCore import Qt, QUrl, QEvent
from PyQt6.QtGui import QDesktopServices, QFontMetrics

import FileHandler
from FileHandler import open_adofai
from MD5Handler import generate_md5


class SongApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("歌曲列表")
        self.setFixedWidth(800)
        self.setMinimumHeight(400)
        self.resize(600, 500)

        # 初始化文件路径
        self.data_file_path = 'resource/levels_info.json'
        self.md5_cache_path = 'resource/workshop_md5_map.json'
        self.custom_data_path = os.path.join(FileHandler.get_steam_install_path(), 'steamapps', 'common',
                                             'A Dance of Fire and Ice', 'User', 'custom_data.sav')

        # 加载歌曲数据
        self.songs = self.load_song_data()
        self.ids = []

        # 初始化数据结构
        self.song_states = self.load_song_states()
        self.group_boxes = {}
        self.song_widgets = {}

        self.init_ui()
        self.create_all_widgets()

    def load_md5_cache(self):
        """加载MD5缓存"""
        try:
            with open(self.md5_cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(self.md5_cache_path, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            return {}

    def save_md5_cache(self, md5_cache):
        """保存MD5缓存"""
        with open(self.md5_cache_path, 'w', encoding='utf-8') as f:
            json.dump(md5_cache, f, ensure_ascii=False, indent=4)

    def load_song_data(self):
        """加载歌曲基本信息"""
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                raw_songs = json.load(f)
                return [song for song in raw_songs if isinstance(song, dict)]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def load_song_states(self):
        """加载歌曲状态数据"""
        try:
            cd = json.load(open(self.custom_data_path, 'r', encoding='utf-8-sig'))
            md5_cache = self.load_md5_cache()
            new_cache = {}

            states = {}
            for song in self.songs:
                workshop_id = song['workshopUrl'].split('&')[0].split('=')[-1]

                if workshop_id in md5_cache:
                    md5 = md5_cache[workshop_id]
                else:
                    author, artist, song_ = open_adofai(workshop_id)
                    if author is None and artist is None and song_ is None:
                        continue
                    md5 = generate_md5(author, artist, song_)
                    new_cache[workshop_id] = md5

                completion = cd.get(f'CustomWorld_{md5}_Completion')
                x_accuracy = cd.get(f'CustomWorld_{md5}_XAccuracy')
                if completion is None:
                    states[song['id']] = 0  # 未玩过
                    continue
                if completion < 1:
                    states[song['id']] = 1  # 进行中
                    continue
                if x_accuracy >= 1:
                    states[song['id']] = 3  # 完美无暇
                    continue
                states[song['id']] = 2  # 完成

            if new_cache:
                md5_cache.update(new_cache)
                self.save_md5_cache(md5_cache)

            return {int(k): self.validate_state(v) for k, v in states.items()}

        except (FileNotFoundError, ValueError) as e:
            logging.error("无法加载自定义数据文件", e)
            return {}

    @staticmethod
    def validate_state(value):
        """确保状态值在0-3之间, 0:未玩过；1：进行中；2：已完成；3：完美无暇"""
        try:
            state = int(value)
            return max(0, min(state, 3))
        except ValueError:
            return 0

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 状态筛选
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("显示状态:"))

        # 添加更多筛选选项
        self.state_filters = {
            0: QCheckBox("未玩过"),
            1: QCheckBox("进行中"),
            2: QCheckBox("已完成"),
            3: QCheckBox("完美无瑕")
        }

        for cb in self.state_filters.values():
            cb.setChecked(True)
            cb.stateChanged.connect(self.update_visibility)
            status_layout.addWidget(cb)

        status_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        main_layout.addLayout(status_layout)

        # 可滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll_area.setWidget(self.scroll_content)

        main_layout.addWidget(scroll_area)
        self.update_visibility()

    def create_all_widgets(self):
        # 按难度分组创建控件
        songs_by_difficulty = {}
        for song in self.songs:
            # 初始化未记录歌曲的状态
            if song['id'] not in self.song_states:
                self.song_states[song['id']] = 0

            diff = song.get("difficulty", 0)
            songs_by_difficulty.setdefault(diff, []).append(song)

        # 创建分组控件
        for difficulty, songs in sorted(songs_by_difficulty.items()):
            group_box = QGroupBox(f"难度 {difficulty}")
            group_layout = QVBoxLayout()
            group_layout.setSpacing(8)

            for song in songs:
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(10)

                # 创建界面元素
                name_label = self.create_name_label(song)
                creators_label = self.create_creators_label(song)
                download_btn = self.create_download_button(song)
                status_combo = self.create_status_combobox(song)

                # 存储控件引用
                self.song_widgets[song['id']] = {
                    'widget': row_widget,
                    'status': status_combo,
                    'difficulty': difficulty
                }

                # 添加布局元素
                row_layout.addWidget(name_label)
                row_layout.addWidget(creators_label)
                row_layout.addWidget(download_btn)
                row_layout.addWidget(status_combo)

                group_layout.addWidget(row_widget)

            group_box.setLayout(group_layout)
            self.group_boxes[difficulty] = group_box
            self.scroll_layout.addWidget(group_box)

        # 添加底部弹簧
        self.scroll_layout.addSpacerItem(QSpacerItem(20, 20,
                                                     QSizePolicy.Policy.Minimum,
                                                     QSizePolicy.Policy.Expanding))

    def create_status_combobox(self, song):
        """创建状态下拉框（替换原来的复选框）"""
        states = {
            0: "未玩过",
            1: "进行中",
            2: "已完成",
            3: "完美无瑕"
        }

        combo = QComboBox()
        combo.addItems(states.values())
        combo.setCurrentIndex(self.song_states.get(song['id'], 0))
        combo.setEnabled(False)
        combo.setFixedWidth(100)
        return combo

    @staticmethod
    def create_name_label(song):
        """创建歌曲名称标签"""
        name_label = QLabel(song["music"]["name"])
        name_label.setToolTip(song["music"]["name"])
        name_label.setMinimumWidth(50)
        name_label.setFixedWidth(220)
        name_label.setStyleSheet("""
                   QLabel {
                       padding-right: 5px;
                       qproperty-alignment: AlignLeft;
                   }
               """)
        fm = QFontMetrics(name_label.font())
        elided_name = fm.elidedText(song["music"]["name"], Qt.TextElideMode.ElideRight, 220)
        name_label.setText(elided_name)
        return name_label

    @staticmethod
    def create_creators_label(song):
        """创建创作者标签"""
        creators = ", ".join(song["music"]["artists"])
        creators_label = QLabel(creators)
        creators_label.setFixedWidth(190)
        creators_label.setToolTip(creators)
        creators_label.setStyleSheet("""
                   QLabel {
                       padding-right: 5px;
                       qproperty-alignment: AlignLeft;
                   }
               """)
        fm = QFontMetrics(creators_label.font())
        elided_creators = fm.elidedText(creators, Qt.TextElideMode.ElideRight, 150)
        creators_label.setText(elided_creators)
        return creators_label

    def create_download_button(self, song):
        """创建下载按钮"""
        download_btn = QPushButton("下载")
        download_btn.setFixedWidth(70)
        download_btn.clicked.connect(
            lambda _, url=song.get("workshopUrl"): self.open_url(url)
        )
        return download_btn

    def update_visibility(self):
        visible_groups = set()
        active_states = [state for state, cb in self.state_filters.items() if cb.isChecked()]

        for song_id, widget_info in self.song_widgets.items():
            current_state = self.song_states.get(song_id, 0)
            is_visible = current_state in active_states

            if is_visible:
                visible_groups.add(widget_info['difficulty'])
            widget_info['widget'].setVisible(is_visible)

        # 更新分组可见性
        for diff, group_box in self.group_boxes.items():
            group_box.setVisible(diff in visible_groups)

        # 处理空列表情况
        empty_label = getattr(self, '_empty_label', None)
        if not visible_groups:
            if not empty_label:
                empty_label = QLabel("没有符合条件的歌曲")
                self._empty_label = empty_label
                self.scroll_layout.insertWidget(0, empty_label)
            empty_label.show()
        elif empty_label:
            empty_label.hide()

    @staticmethod
    def open_url(url):
        if url and url.startswith(("http://", "https://")):
            QDesktopServices.openUrl(QUrl(url))

    def closeEvent(self, event):
        """窗口关闭时确保保存最后状态"""
        event.accept()

    def changeEvent(self, event):
        if event.type() == 99:
            self.song_states = self.load_song_states()
            for song_id, song_state in self.song_states.items():
                if song_id in self.song_widgets:
                    self.song_widgets[song_id]['status'].setCurrentIndex(song_state)
        super().changeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SongApp()
    window.show()
    sys.exit(app.exec())