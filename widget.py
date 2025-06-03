from PyQt6.QtCore import Qt, QUrl, QRect, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFontMetrics, QDesktopServices, QPainter
from PyQt6.QtWidgets import QComboBox, QLabel, QPushButton, QCheckBox, QStyle, QLineEdit


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
