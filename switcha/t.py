import string

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from window import Windows

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        self.wnds = Windows()
        self.wnds.show()

    def keyPressEvent(self, ev):
        ch = str(ev.text())
        idx = ord(ch) - ord('1')
        if 1 <= idx <= 9:
            self.wnds.switch_to(idx, activate=False)
            self.wnds.show()
        elif ch in string.lowercase:
            self.wnds.update()
            self.wnds.show()
        return super(Widget, self).keyPressEvent(ev)

app = QApplication([])
w = Widget()
w.show()
app.exec_()
