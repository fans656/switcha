import string

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from window import Windows

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.wnds = Windows()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_windows)
        self.timer.start(100)

    def keyPressEvent(self, ev):
        #if ev.text() == 'j':
        #    self.update_windows()
        return super(Widget, self).keyPressEvent(ev)

    def update_windows(self):
        self.wnds.update()
        self.update()

    def paintEvent(self, ev):
        painter = QPainter(self)
        fm = painter.fontMetrics()
        linespacing = 2 * fm.lineSpacing()
        for i, wnd in enumerate(self.wnds):
            title = wnd.title
            mark = '*' if wnd.current else ' '
            text = u'{} {}'.format(mark, title)
            painter.drawText(50, 30 + i * linespacing, text)

app = QApplication([])
w = Widget()
w.resize(480, 640)
w.move(1366 / 2.0, 0)
w.show()
app.exec_()
