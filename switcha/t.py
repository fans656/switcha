from window import Windows

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        wnds = Windows()
        for wnd in wnds:
            im = wnd.icon

app = QApplication([])
w = Widget()
#w.show()
app.exec_()
