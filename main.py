import logging
import sys

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox,
    QScrollArea, QSizePolicy, QSpacerItem
)

import FileHandler
from MD5Handler import generate_md5
from widget import *


class SongApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("歌曲列表")
        self.setFixedWidth(800)
        self.setMinimumHeight(400)
        self.resize(600, 500)

        # 加载歌曲数据
        self.songs = FileHandler.load_song_data()
        self.ids = []

        # 初始化数据结构
        self.song_states = self.load_song_states()
        self.btn_status = FileHandler.load_status_data()
        self.group_boxes = {}
        self.song_widgets = []

        self.scroll_layout = None
        self.state_filters = None
        self.count_label = None
        self.rks_label = None

        self.init_ui()
        self.create_all_widgets()

    def load_song_states(self):
        """加载歌曲状态数据"""
        try:
            cd = FileHandler.load_custom_data()
            md5_cache = FileHandler.load_md5_cache()
            new_cache = {}

            states = {}
            for song in self.songs:
                workshop_id = song['workshopUrl'].split('&')[0].split('=')[-1]

                if workshop_id in md5_cache:
                    md5 = md5_cache[workshop_id]
                else:
                    author, artist, song_ = FileHandler.open_adofai(workshop_id)
                    if author is None and artist is None and song_ is None:
                        continue
                    md5 = generate_md5(author, artist, song_)
                    new_cache[workshop_id] = md5

                completion = cd.get(f'CustomWorld_{md5}_Completion')
                x_accuracy = cd.get(f'CustomWorld_{md5}_XAccuracy')
                if completion is None:
                    states[song['id']] = (0, 0)  # 未玩过
                    continue
                if completion < 1:
                    states[song['id']] = (1, completion)  # 进行中
                    continue
                if x_accuracy >= 1:
                    states[song['id']] = (3, 0)  # 完美无暇
                    continue
                states[song['id']] = (2, x_accuracy)  # 完成

            if new_cache:
                md5_cache.update(new_cache)
                FileHandler.save_md5_cache(md5_cache)

            return {int(k): v for k, v in states.items()}

        except (FileNotFoundError, ValueError) as e:
            logging.error("无法加载自定义数据文件", e)
            return {}

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 状态筛选
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("显示状态:"))


        # 添加更多筛选选项
        self.state_filters = {
            0: FilterCheckBox(status_layout, text='未玩过', checked=self.btn_status['data'][0], change_connect=self.update_visibility),
            1: FilterCheckBox(status_layout, text='进行中', checked=self.btn_status['data'][1], change_connect=self.update_visibility),
            2: FilterCheckBox(status_layout, text='已完成', checked=self.btn_status['data'][2], change_connect=self.update_visibility),
            3: FilterCheckBox(status_layout, text='完美无瑕', checked=self.btn_status['data'][3], change_connect=self.update_visibility)
        }

        sort_com = ComboBox()
        sort_com.addItems(["难度", "歌曲名"])
        status_layout.addWidget(sort_com)

        self.count_label = QLabel("歌曲: 0")
        status_layout.addWidget(self.count_label)

        status_layout.addWidget(self.rks_label)
        status_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.rks_label = QLabel("RKS: 0")
        status_layout.addWidget(self.rks_label)

        main_layout.addLayout(status_layout)

        # 可滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll_area.setWidget(scroll_content)

        main_layout.addWidget(scroll_area)

    def create_all_widgets(self):
        # 按难度分组创建控件
        songs_by_difficulty = {}
        for song in self.songs:
            # 初始化未记录歌曲的状态
            if song['id'] not in self.song_states:
                self.song_states[song['id']] = (0, 0)

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
                name_label = NameLabel(text=song["music"]["name"])
                creators_label = ArtistsLabel(text=", ".join(song["music"]["artists"]))
                download_btn = DownloadButton(url=song["workshopUrl"])
                status_label = StatusLabel()
                status_type = 0

                # 存储控件引用
                self.song_widgets.append({
                    'id': song['id'],
                    'name': song['name'],
                    'widget': row_widget,
                    'difficulty': difficulty,
                    'status_type': status_type,
                    'status_label': status_label
                })

                # 添加布局元素
                row_layout.addWidget(name_label)
                row_layout.addWidget(creators_label)
                row_layout.addWidget(download_btn)
                row_layout.addWidget(status_label)

                group_layout.addWidget(row_widget)

            group_box.setLayout(group_layout)
            self.group_boxes[difficulty] = group_box
            self.scroll_layout.addWidget(group_box)

        # 添加底部弹簧
        self.scroll_layout.addSpacerItem(QSpacerItem(20, 20,
                                                     QSizePolicy.Policy.Minimum,
                                                     QSizePolicy.Policy.Expanding))

    def update_visibility(self):
        """更新歌曲列表的可见性"""
        visible_count = 0
        visible_groups = set()
        active_states = [state for state, cb in self.state_filters.items() if cb.isChecked()]

        self.song_widgets = sorted(self.song_widgets, key=lambda song_info: song_info['name'] , reverse=True)

        for widget_info in self.song_widgets:
            song_id = widget_info['id']
            current_state = self.song_states.get(song_id, (0, 0))[0]
            is_visible = current_state in active_states

            if is_visible:
                visible_count += 1
                visible_groups.add(widget_info['difficulty'])
            widget_info['widget'].setVisible(is_visible)

        self.count_label.setText(f"歌曲: {visible_count}")

        # 更新分组可见性
        for diff, group_box in self.group_boxes.items():
            group_box.setVisible(diff in visible_groups)

        # 处理空列表情况
        empty_label = getattr(self, '_empty_label', None)
        if not visible_groups:
            if not empty_label:
                empty_label = QLabel("没有符合条件的歌曲")
                setattr(self, '_empty_label', empty_label)
                self.scroll_layout.insertWidget(0, empty_label)
            empty_label.show()
        elif empty_label:
            if empty_label:
                empty_label.hide()

        # 保存状态
        self.btn_status = {'data': [cb.isChecked() for state, cb in self.state_filters.items()]}
        FileHandler.save_status_data(self.btn_status)

    def refresh_song_states(self):
        """刷新歌曲状态"""
        rks_list = []
        for widget_info in self.song_widgets:
            song_id = widget_info['id']
            if song_id in self.song_states:
                status, progress = self.song_states[song_id]
                text = '未玩过'
                difficulty = widget_info['difficulty']
                if status == 1:
                    text = f'progress: {progress * 100: .2f}%'
                    widget_info['status_label'].setStyleSheet("color: qlineargradient(x1: 0, y1: 0,    x2: 1, y2: 1,    stop: 0 #66e, stop: 1 #007FFF);")
                elif status == 2:
                    text = f'x_a: {progress * 100: .2f}%'
                    widget_info['status_label'].setStyleSheet("color: qlineargradient(x1: 0, y1: 0,    x2: 1, y2: 1,    stop: 0 #66e, stop: 1 #FFD700);")
                    rks_list.append(difficulty * progress * progress)
                elif status == 3:
                    text = '完美无瑕'
                    widget_info['status_label'].setStyleSheet("color: qlineargradient(x1: 0, y1: 0,    x2: 1, y2: 1,    stop: 0 #66e, stop: 1 #fd3e7f);")
                    rks_list.append(difficulty)
                widget_info['status_type'] = status
                widget_info['status_label'].setText(text)
        average = 0
        if rks_list:
            sorted_rks_list = sorted(rks_list, reverse=True)
            average = sum(sorted_rks_list[:20]) / 20

        self.rks_label.setText(f'RKS: {average:.2f}')

    def closeEvent(self, event):
        """窗口关闭时确保保存最后状态"""
        event.accept()

    def changeEvent(self, event):
        """当窗口最小化或恢复时重新加载状态"""
        if event.type() == 99:
            self.song_states = self.load_song_states()
            self.refresh_song_states()

            self.update_visibility()
        super().changeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SongApp()
    window.show()
    sys.exit(app.exec())