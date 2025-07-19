import logging
import sys

from PyQt6.QtWidgets import (
    QSizePolicy, QSpacerItem
)

import FileHandler
from MD5Handler import generate_md5
from widget import *


class SongApp(QWidget):
    def __init__(self):
        self.toast = None
        super().__init__()

        self.setWindowTitle("歌曲列表")
        self.setFixedWidth(800)
        self.setMinimumHeight(400)
        self.resize(600, 500)

        # 加载歌曲数据
        self.songs = FileHandler.load_song_data()
        self.ids = []

        # 初始化数据结构
        self.btn_status = FileHandler.load_status_data()
        self.stars = FileHandler.load_stars()
        self.group_boxes = {}
        self.song_widgets = []

        self.sort_com = None
        self.search_entry = None
        self.scroll_widget = None
        self.state_filters = None
        self.count_label = None
        self.rks_label = None
        self.scroll_area = None

        self.init_ui()
        self.create_all_widgets()

        self.load_song_states()

    def load_song_states(self):
        """加载歌曲状态数据"""
        try:
            cd = FileHandler.load_custom_data()
            md5_cache = FileHandler.load_md5_cache()
            new_cache = {}

            for song in self.songs:
                song_id = song['id']
                widget = None
                for w in self.song_widgets:
                    if w['id'] == song_id:
                        widget = w
                        break
                if not widget:
                    continue
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
                    widget['status'] = (0, 0)  # 未玩过
                    continue
                if completion < 1:
                    widget['status'] = (1, completion)  # 进行中
                    continue
                if x_accuracy >= 1:
                    widget['status'] = (3, 0)  # 完美无暇
                    widget['rks'] = widget['difficulty']
                    continue
                widget['status'] = (2, x_accuracy)  # 完成
                widget['rks'] = widget['difficulty'] * widget['status'][1] * widget['status'][1]

            if new_cache:
                md5_cache.update(new_cache)
                FileHandler.save_md5_cache(md5_cache)

        except (FileNotFoundError, ValueError) as e:
            logging.error("无法加载自定义数据文件", e)

    def init_ui(self):
        # 菜单选项
        menu_widget = QWidget(self)
        menu_widget.move(0, 0)
        menu_widget.resize(self.width(), 50)
        menu_layout = QHBoxLayout(menu_widget)

        menu_layout.addWidget(QLabel("显示状态:"))

        # 添加更多筛选选项
        self.state_filters = {
            0: FilterCheckBox(
                menu_layout,
                text='未玩过',
                checked=self.btn_status['data'][0],
                change_connect=self.update_visibility
            ),
            1: FilterCheckBox(
                menu_layout,
                text='进行中',
                checked=self.btn_status['data'][1],
                change_connect=self.update_visibility
            ),
            2: FilterCheckBox(
                menu_layout,
                text='已完成',
                checked=self.btn_status['data'][2],
                change_connect=self.update_visibility
            ),
            3: FilterCheckBox(
                menu_layout,
                text='完美无瑕',
                checked=self.btn_status['data'][3],
                change_connect=self.update_visibility
            ),
            4: FilterCheckBox(
                menu_layout,
                text='已收藏',
                checked=self.btn_status['data'][4],
                change_connect=self.update_visibility
            ),
        }

        self.sort_com = ComboBox()
        self.sort_com.addItems([
            SortEnum.DIFFICULTY,
            SortEnum.NAME,
            SortEnum.ARTISTS,
            SortEnum.RKS
        ])
        self.sort_com.currentIndexChanged.connect(self.update_sorted_list)
        menu_layout.addWidget(self.sort_com)

        self.search_entry = SearchEntry()
        self.search_entry.textChanged.connect(self.update_visibility)
        menu_layout.addWidget(self.search_entry)

        self.count_label = QLabel("歌曲: 0")
        menu_layout.addWidget(self.count_label)

        menu_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.rks_label = QLabel("RKS: 0")
        menu_layout.addWidget(self.rks_label)

        self.scroll_widget = ScrollContentWidget(self)
        self.scroll_widget.move(0, 50)
        self.scroll_widget.resize(self.width(), self.height() - 50)

    def create_all_widgets(self):
        for song in self.songs:
            # 获取谱子一些数据
            song_id = song['id']
            music_name = song["music"]["name"]
            music_artists = ", ".join(song["music"]["artists"])
            workshop_url = song["workshopUrl"]
            difficulty = song.get("difficulty", 0)
            status = (0, 0)
            rks = 0

            # 创建界面元素
            name_label = NameLabel(text=music_name, main=self)
            creators_label = ArtistsLabel(text=music_artists)
            is_star = song_id in self.stars
            stars_button = StarsButton(song_id=song_id, is_star=is_star)
            download_btn = DownloadButton(url=workshop_url)
            status_label = StatusLabel()

            row_widget = RowWidget()
            row_widget.setFixedWidth(self.width())
            row_widget.add_widget(name_label)
            row_widget.add_widget(creators_label)
            row_widget.add_widget(stars_button)

            row_widget.add_widget(download_btn)
            row_widget.add_widget(status_label)

            # 存储控件引用
            self.song_widgets.append({
                'id': song_id,
                'name': music_name,
                'widget': row_widget,
                'artists': music_artists,
                'difficulty': difficulty,
                'status': status,
                'status_label': status_label,
                'rks': rks,
                'stars_button': stars_button,
                'is_star': is_star
            })
        self.scroll_widget.update_info(self.song_widgets, SortEnum.DIFFICULTY)

    def update_sorted_list(self):
        """ 更新歌曲列表的排序 """
        current_sort = self.sort_com.currentText()
        sort_order = self.sort_com.sort_order

        # 根据排序方式排序数据
        if current_sort == SortEnum.NAME:
            self.song_widgets = sorted(self.song_widgets, key=lambda x: x['name'], reverse=sort_order)
        elif current_sort == SortEnum.ARTISTS:
            self.song_widgets = sorted(self.song_widgets, key=lambda x: x['artists'], reverse=sort_order)
        elif current_sort == SortEnum.RKS:
            self.song_widgets = sorted(self.song_widgets, key=lambda x: x['rks'], reverse=sort_order)
        else:
            self.song_widgets = sorted(self.song_widgets, key=lambda x: x['difficulty'], reverse=sort_order)

        self.update_visibility()

    def update_visibility(self):
        """更新歌曲列表的可见性"""
        visible_count = 0
        search_text = self.search_entry.text()
        active_states = [state for state, cb in self.state_filters.items() if cb.isChecked()]
        current_sort = self.sort_com.currentText()

        # 获取收藏筛选状态
        show_stars = self.state_filters[4].isChecked()

        data = []

        # 处理歌曲行可见性及布局
        for idx, widget_info in enumerate(self.song_widgets):
            current_state = widget_info['status'][0]
            widget_text = widget_info['name'] + '\t' + widget_info['artists']

            is_visible = (
                    current_state in active_states and
                    search_text.lower() in widget_text.lower() and
                    (not show_stars or widget_info['is_star'])
            )

            widget_info['widget'].setVisible(False)

            if is_visible:
                data.append(widget_info)
                visible_count += 1

        self.count_label.setText(f"歌曲: {visible_count}")

        self.scroll_widget.update_info(data, current_sort)

        # 保存状态
        self.btn_status = {'data': [cb.isChecked() for state, cb in self.state_filters.items()]}
        FileHandler.save_status_data(self.btn_status)

    def refresh_song_states(self):
        """刷新歌曲状态"""
        rks_list = []
        for widget_info in self.song_widgets:
            status, progress = widget_info['status']
            text = '未玩过'
            difficulty = widget_info['difficulty']
            if status == 1:
                text = f'progress: {progress * 100: .2f}%'
                widget_info['status_label'].setStyleSheet(
                    "color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #66e, stop: 1 #007FFF);"
                )
            elif status == 2:
                text = f'x_a: {progress * 100: .2f}%'
                widget_info['status_label'].setStyleSheet(
                    "color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #66e, stop: 1 #FFD700);"
                )
                widget_info['status_label'].setToolTip(f'rks: {difficulty * progress * progress:.2f}')
                rks_list.append(difficulty * progress * progress)
            elif status == 3:
                text = '完美无瑕'
                widget_info['status_label'].setStyleSheet(
                    "color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #66e, stop: 1 #fd3e7f);"
                )
                widget_info['status_label'].setToolTip(f'rks: {difficulty:.2f}')
                rks_list.append(difficulty)
            widget_info['status_label'].setText(text)
        average = 0
        if rks_list:
            sorted_rks_list = sorted(rks_list, reverse=True)
            average = sum(sorted_rks_list[:20]) / 20

        self.rks_label.setText(f'RKS: {average:.2f}')

    def refresh_song_stars(self, song_id, is_stars):
        """处理收藏状态变化"""
        if is_stars:
            if song_id not in self.stars:
                self.stars.append(song_id)
        else:
            if song_id in self.stars:
                self.stars.remove(song_id)

        for widget_info in self.song_widgets:
            if widget_info['id'] == song_id:
                widget_info['is_star'] = is_stars
                widget_info['stars_button'].update_icon()
                break

        FileHandler.save_stars(self.stars)
        self.update_visibility()  # 确保UI刷新

    def show_toast(self, text=''):
        if self.toast is None:
            self.toast = ToastWidget(self)
        self.toast.set_text(text)
        self.toast.show()

    def changeEvent(self, event):
        """当窗口最小化或恢复时重新加载状态"""
        if event.type() == 99:
            self.load_song_states()
            self.refresh_song_states()

            self.update_visibility()

        super().changeEvent(event)

    def resizeEvent(self, a0):
        self.scroll_widget.resize(self.width(), self.height() - 50)
        super().resizeEvent(a0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SongApp()
    window.show()
    sys.exit(app.exec())

