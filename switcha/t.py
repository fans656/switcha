import string

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from window import RendableWindows

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        wnds = RendableWindows(self)
        for wnd in wnds:
            if not wnd:
                print ''
            else:
                print wnd.width, wnd.height, wnd.title

app = QApplication([])
w = Widget()
w.show()
app.exec_()
