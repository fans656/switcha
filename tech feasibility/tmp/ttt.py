import time
import ctypes
import win32api
import win32con
from f6.win32 import vk2name

def get_downs():
    downs = win32api.GetKeyboardState()
    downs = map(ord, downs)
    downs = [(vk2name(vk), vk)
             for vk, down in enumerate(downs) if down >> 7]
    return downs

def print_downs():
    print ' '.join(t for t, _ in get_downs())

from PySide.QtCore import *
from PySide.QtGui import *

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        self.timer = QTimer()
        self.timer.timeout.connect(print_downs)
        self.timer.start(100)

app = QApplication([])
w = Widget()
w.show()
app.exec_()
