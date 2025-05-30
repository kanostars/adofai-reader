from PyQt6.QtCore import Qt, QUrl, QRect, pyqtSignal
from PyQt6.QtGui import QFontMetrics, QDesktopServices, QPainter
from PyQt6.QtWidgets import QComboBox, QLabel, QPushButton, QCheckBox, QStyle


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



class ComboBox(QComboBox):
    """
    用于排序的下拉框
    """
    sort_change_event = pyqtSignal()
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
        # 计算按钮区域
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
            self.currentIndexChanged.emit(self.currentIndex())  # 触发排序更新
            self.sort_change_event.emit()
        else:
            # 点击本体：显示下拉列表
            super().mousePressEvent(event)


class StatusLabel(QLabel):
    """
    歌曲状态标签
    """
    def __init__(self, parent=None, flags=None):
        super().__init__(parent, flags)

        self.setText('未玩过')
        self.setFixedWidth(100)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class NameLabel(QLabel):
    """
    歌曲名称标签
    """
    def __init__(self, parent=None, flags=None, text=None):
        super().__init__(parent, flags)

        self.setToolTip(text)
        self.setMinimumWidth(50)
        self.setFixedWidth(220)
        self.setStyleSheet('padding-right: 5px;qproperty-alignment: AlignLeft;')
        fm = QFontMetrics(self.font())
        elided_name = fm.elidedText(text, Qt.TextElideMode.ElideRight, 220)
        self.setText(elided_name)

class ArtistsLabel(QLabel):
    """
    歌曲作者标签
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
    歌曲下载按钮
    """
    def __init__(self, parent=None, flags=None, url=None):
        super().__init__(parent, flags)

        self.setFixedWidth(70)
        self.setText('下载')
        self.url = url

    def mouseReleaseEvent(self, event):
        if self.url and self.url.startswith(("http://", "https://")):
            QDesktopServices.openUrl(QUrl(self.url))
