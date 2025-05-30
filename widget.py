from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFontMetrics, QDesktopServices
from PyQt6.QtWidgets import QComboBox, QLabel, QPushButton, QCheckBox


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
    def wheelEvent(self, event):
        event.ignore()


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
