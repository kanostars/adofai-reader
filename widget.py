import os.path

from PyQt6.QtCore import Qt, QUrl, QRect, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFontMetrics, QDesktopServices, QPainter
from PyQt6.QtWidgets import QComboBox, QLabel, QPushButton, QCheckBox, QStyle, QLineEdit, QWidget, QHBoxLayout, \
    QGraphicsOpacityEffect, QScrollBar, QApplication

from enums import *
import FileHandler
import global_var


class FilterCheckBox(QCheckBox):
    """
    用于筛选的复选框
    """

    def __init__(self, parent=None, text=None, checked=True, change_connect=None):
        super().__init__(None)

        self.setText(text)
        self.setChecked(checked)
        if change_connect:
            self.stateChanged.connect(change_connect)
        if parent:
            parent.addWidget(self)

        fm = QFontMetrics(self.font())
        self.text_width = fm.horizontalAdvance(text)  # 文字内容宽度
        style = self.style()
        # 获取勾选框宽度和默认间距（根据当前样式）
        self.checkbox_width = style.pixelMetric(QStyle.PixelMetric.PM_IndicatorWidth)
        self.spacing = style.pixelMetric(QStyle.PixelMetric.PM_CheckBoxLabelSpacing)
        # 初始宽度
        self.initial_width = self.checkbox_width + self.spacing
        # 展开宽度
        self.expanded_width = self.initial_width + self.text_width + self.spacing

        # 初始化固定宽度为初始状态
        self.setFixedWidth(self.initial_width)

        # 初始化动画（使用minimumWidth属性实现平滑过渡）
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)  # 200ms动画时长
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)  # 缓动效果

    def enterEvent(self, event):
        """鼠标进入时展开宽度"""
        self.animation.setStartValue(self.minimumWidth())
        self.animation.setEndValue(self.expanded_width)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时收缩宽度"""
        self.animation.setStartValue(self.minimumWidth())
        self.animation.setEndValue(self.initial_width)
        self.animation.start()
        super().leaveEvent(event)


class ComboBox(QComboBox):
    """
    用于排序的下拉框
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sort_order = False
        self.button_width = 20

    def wheelEvent(self, event):
        event.ignore()

    def paintEvent(self, event):
        """重写绘制事件：添加方向图标"""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 计算按钮区域（右侧固定宽度）
        button_rect = QRect(
            self.width() - self.button_width,
            0,
            self.button_width,
            self.height()
        )

        # 绘制方向图标（↑/↓）
        icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_ArrowUp if self.sort_order else QStyle.StandardPixmap.SP_ArrowDown
        )
        icon_size = icon.actualSize(button_rect.size())
        icon_rect = QRect(
            button_rect.center().x() - icon_size.width() // 2,
            button_rect.center().y() - icon_size.height() // 2,
            icon_size.width(),
            icon_size.height()
        )
        icon.paint(painter, icon_rect)

    def mousePressEvent(self, event):
        """重写鼠标点击事件：区分按钮点击和本体点击"""
        button_rect = QRect(
            self.width() - self.button_width,
            0,
            self.button_width,
            self.height()
        )

        if button_rect.contains(event.pos()):
            # 点击按钮：切换排序方向
            self.sort_order = not self.sort_order
            self.update()  # 刷新图标
            self.currentIndexChanged.emit(self.currentIndex())
        else:
            # 点击本体：显示下拉列表
            super().mousePressEvent(event)


class SearchEntry(QLineEdit):
    """
    搜索框
    """

    def __init__(self, parent=None, initial_width=40, expanded_width=80):
        super().__init__(parent)
        # 基础设置
        self.setPlaceholderText("搜索")
        self.setClearButtonEnabled(True)

        # 宽度参数（可通过参数自定义）
        self.setFixedWidth(initial_width)
        self.initial_width = initial_width  # 闲置时宽度
        self.expanded_width = expanded_width  # 聚焦时宽度
        self.setMinimumWidth(self.initial_width)  # 初始最小宽度

        # 初始化动画（使用minimumWidth属性实现平滑过渡）
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)  # 200ms动画时长
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)  # 缓动效果

    def focusInEvent(self, event):
        """获得焦点时展开宽度"""
        self.setClearButtonEnabled(True)
        self.animation.setStartValue(self.minimumWidth())
        self.animation.setEndValue(self.expanded_width)
        self.animation.start()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        """失去焦点时收缩宽度"""
        self.setClearButtonEnabled(False)
        self.animation.setStartValue(self.minimumWidth())
        self.animation.setEndValue(self.initial_width)
        self.animation.start()
        super().focusOutEvent(event)


class StatusLabel(QLabel):
    """
    打谱完成度标签
    """

    def __init__(self, parent=None, flags=None):
        super().__init__(parent, flags)

        self.setText('未玩过')
        self.setFixedWidth(100)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class NameLabel(QLabel):
    """
    音乐名称标签
    """

    def __init__(self, parent=None, text=None):
        super().__init__(parent)

        self.text = text

        self.setToolTip(text + '（右键以复制）')
        self.setMinimumWidth(50)
        self.setFixedWidth(220)
        self.setStyleSheet('padding-right: 5px;qproperty-alignment: AlignLeft;')
        fm = QFontMetrics(self.font())
        elided_name = fm.elidedText(text, Qt.TextElideMode.ElideRight, 220)
        self.setText(elided_name)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            QApplication.clipboard().setText(self.text)
            if global_var.global_window:
                global_var.global_window.show_toast('已复制')


class ArtistsLabel(QLabel):
    """
    乐曲作者标签
    """

    def __init__(self, parent=None, flags=None, text=None):
        super().__init__(parent, flags)

        self.setFixedWidth(190)
        self.setToolTip(text)
        self.setStyleSheet('padding-right: 5px;qproperty-alignment: AlignLeft;')
        fm = QFontMetrics(self.font())
        elided_creators = fm.elidedText(text, Qt.TextElideMode.ElideRight, 150)
        self.setText(elided_creators)


class DownloadButton(QPushButton):
    """
    谱子下载按钮
    """

    def __init__(self, parent=None, flags=None, url=None):
        super().__init__(parent, flags)

        self.setFixedWidth(70)
        self.setText('下载')
        self.url = url.strip()

    def mouseReleaseEvent(self, event):
        if self.url and self.url.startswith(("http://", "https://")):
            workshop_id = self.url.split('&')[0].split('=')[-1]
            if os.path.exists(FileHandler.get_adofai_path(workshop_id)):
                if global_var.global_window and global_var.global_window.socket_handler.is_connected():
                    global_var.global_window.socket_handler.play(FileHandler.get_adofai_path(workshop_id))
                    global_var.global_window.showMinimized()
                else:
                    global_var.global_window.show_toast('模组连接失败')
            else:
                global_var.global_window.show_toast('已打开网页，请手动订阅')
                QDesktopServices.openUrl(QUrl(self.url))


class RowWidget(QWidget):
    """
    歌曲行
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.row_layout = QHBoxLayout(self)
        self.row_layout.setContentsMargins(0, 0, 0, 0)
        self.row_layout.setSpacing(10)

        self.opacity_effect = QGraphicsOpacityEffect(self)

    def add_widget(self, widget):
        self.row_layout.addWidget(widget)

    def set_opacity(self, opacity):
        self.opacity_effect.setOpacity(opacity)
        self.setGraphicsEffect(self.opacity_effect)


class DifficultyLabel(QLabel):
    """
    难度标签
    """

    def __init__(self, parent=None, difficulty=0):
        super().__init__(parent)
        self.parent = parent
        self.difficulty = difficulty

        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.is_hide = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_hide = not self.is_hide
            if self.is_hide:
                self.parent.hide_difficulty.append(self.difficulty)
            else:
                self.parent.hide_difficulty.remove(self.difficulty)
            self.parent.refresh_window()
            self.parent._update_scrollbar()


class ScrollContentWidget(QWidget):
    """
    自定义可滚动控件
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.data = []
        self.hide_difficulty = []
        self.pos = 0
        self.final_pos = 0
        self.difficulty_label_dict = {}

        self.sort_text = SortEnum.DIFFICULTY
        self.delta = 30
        self.item_height = 30
        self.total_label_delta = 0
        self.show_item = self.height() // self.item_height + 1

        self.difficulty_label = QLabel(self)
        self.difficulty_label.move(30, 0)
        self.difficulty_label.setFixedWidth(self.width() - 30)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate_step)
        self.anim_speed = 16

        self.scrollbar = QScrollBar(Qt.Orientation.Vertical, self)
        self.scrollbar.valueChanged.connect(self._handle_scrollbar)

        self.is_scrolling = False  # 新增滚动状态标志
        self.scrollbar.sliderPressed.connect(lambda: setattr(self, 'is_scrolling', True))
        self.scrollbar.sliderReleased.connect(lambda: setattr(self, 'is_scrolling', False))

    def animate_step(self):
        """每一帧的动画更新"""
        current_pos = self.pos
        new_pos = int((self.final_pos - current_pos) / 5 + current_pos)

        if abs(new_pos - current_pos) < 1:
            self.anim_timer.stop()

        self.pos = new_pos
        self.refresh_window()

    def update_info(self, data, sort_text):
        self.data = data
        self.update_pos()
        self.sort_text = sort_text

    def refresh_window(self):
        pos = self.pos
        for difficulty_label in self.difficulty_label_dict.values():
            difficulty_label.hide()

        if self.sort_text == SortEnum.DIFFICULTY:
            self.difficulty_label.show()
            self.delta = 30
        else:
            self.difficulty_label.hide()
            self.delta = 0

        label_delta = 0
        first_finish = False
        last_difficulty = 0
        for index, song_row in enumerate(self.data):
            widget = song_row.get('widget')

            difficulty = song_row.get('difficulty')
            if difficulty != last_difficulty:
                last_difficulty = difficulty

                if self.sort_text == SortEnum.DIFFICULTY:
                    if pos + self.item_height * index + label_delta > 0:
                        difficulty_label = self.difficulty_label_dict.get(difficulty)
                        if not difficulty_label:
                            difficulty_label = DifficultyLabel(self, difficulty)
                            difficulty_label.setFixedWidth(self.width() - 35 - 12)
                            difficulty_label.setText(
                                f'-------------------------------------------------------------------难度{difficulty}------------------------------------------------------------------')
                            self.difficulty_label_dict[difficulty] = difficulty_label
                        difficulty_label.move(35, int(pos + self.item_height * index + label_delta))
                        difficulty_label.show()

                    label_delta += self.item_height

            widget.setParent(self)

            if difficulty in self.hide_difficulty and self.sort_text == SortEnum.DIFFICULTY:
                label_delta -= self.item_height
                widget.hide()
            else:
                widget_y = int(pos + self.item_height * index + label_delta)

                if widget_y > self.height() or widget_y + self.item_height - self.delta < 0:
                    widget.hide()
                else:
                    if not first_finish:
                        first_finish = True
                        self.difficulty_label.setText(f'难度：{song_row.get("difficulty")}')
                    if widget_y < self.delta:
                        delta = int(self.delta - widget_y)
                        widget.move(delta, widget_y)
                        widget.setFixedWidth(self.width() - delta * 2 - 12)
                        opacity = 1 / delta
                        widget.set_opacity(opacity)
                    elif widget_y + self.item_height > self.height():
                        delta = int(widget_y + self.item_height - self.height())
                        widget.move(delta, widget_y)
                        widget.setFixedWidth(self.width() - delta * 2 - 12)
                        opacity = 1 / delta
                        widget.set_opacity(opacity)
                    else:
                        widget.move(0, widget_y)
                        widget.setFixedWidth(self.width() - 12)
                        widget.set_opacity(1)
                    widget.show()

        self.total_label_delta = label_delta

    def update_pos(self):
        if len(self.data) * self.item_height < self.height() or self.final_pos > self.delta:
            self.final_pos = self.delta
        elif self.final_pos < self.height() - len(self.data) * self.item_height - self.total_label_delta - 10:
            self.final_pos = self.height() - len(self.data) * self.item_height - self.total_label_delta - 10

        if not self.anim_timer.isActive():
            self.anim_timer.start(self.anim_speed)

        self._update_scrollbar()

    def _update_scrollbar(self):
        """更新滚动条范围和位置"""

        content_height = len(self.data) * self.item_height + self.total_label_delta + 10
        viewport_height = self.height()

        self.scrollbar.setMaximum(max(0, content_height - viewport_height))
        self.scrollbar.setPageStep(viewport_height)
        self.scrollbar.setVisible(content_height > viewport_height)

        if not self.is_scrolling:
            self.scrollbar.setValue(-int(self.final_pos))

    def _handle_scrollbar(self, value):
        """滚动条拖动事件处理"""

        self.final_pos = -value
        self.update_pos()

    def wheelEvent(self, a0):
        self.final_pos += a0.angleDelta().y() / 2
        self.update_pos()

    def resizeEvent(self, a0):
        self.show_item = self.height() // self.item_height + 1
        self.scrollbar.resize(12, self.height())
        self.scrollbar.move(self.width() - 12, 0)
        self._update_scrollbar()
        self.update_pos()


class ToastWidget(QWidget):
    """
    toast提示框
    """

    def __init__(self, parent=None):
        super(ToastWidget, self).__init__(parent)

        self.setGeometry(parent.width() // 2 - 50, -50, 200, 30)

        self.back_label = QLabel(self)
        self.back_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.back_label.setStyleSheet(
            "color: white; background-color: rgba(0, 0, 0, 120); padding: 10px; border-radius: 10px;")
        self.back_label.setGeometry(0, 0, self.width(), self.height())

        # 实现弹出的动画
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.hide)

    def set_text(self, text):
        self.back_label.setText(text)

    def hide(self):
        self.animation.stop()
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(QRect(self.x(), -self.height(), self.width(), self.height()))
        self.animation.start()
        self.timer.stop()

    def show(self):
        self.raise_()
        self.animation.stop()
        self.animation.setStartValue(QRect(self.x(), -self.height(), self.width(), self.height()))
        self.animation.setEndValue(QRect(self.x(), 50, self.width(), self.height()))
        self.animation.start()
        self.timer.start()


class StarsButton(QPushButton):
    """收藏按钮"""

    def __init__(self, parent=None, song_id=None, is_star=False):
        super().__init__(parent)
        self.song_id = song_id
        self.is_star = is_star
        self.setFixedWidth(20)
        self.update_icon()

    def update_icon(self):
        """更新按钮图标"""

        if self.is_star:
            self.setText('★')
            self.setStyleSheet("background: transparent; border: none; color: gold; font-size: 16px;")
        else:
            self.setText('☆')
            self.setStyleSheet("background: transparent; border: none; color: gray; font-size: 16px;")

    def toggle_star(self):
        """切换收藏状态"""
        self.is_star = not self.is_star
        self.update_icon()

        main_window = self.window()
        if hasattr(main_window, 'refresh_song_stars'):
            main_window.refresh_song_stars(self.song_id, self.is_star)

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_star()
        super().mouseReleaseEvent(event)
