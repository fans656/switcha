'''
(win32api.GetKeyboardState)[1] will retrive the status of the 256 virtual keys
It's based on message queue. For normal application, the key stroke events are
posted to the thread when your window is active, or something else.
So you should hook the keyboard in order to get the real keyboard state.

[1]: https://msdn.microsoft.com/en-us/library/windows/desktop/ms646299(v=vs.85).aspx
'''
import time

import win32api
import win32con
from PySide.QtCore import *
from PySide.QtGui import *

vk2name = {getattr(win32con, name): name[3:] for name in dir(win32con)
           if name.startswith('VK_')}
name2vk = {name: vk for vk, name in vk2name.items()}

def get_states():
    r = win32api.GetKeyboardState()
    r = map(ord, r)
    return r

def get_keys(states):
    return tuple(i for i, state in enumerate(states) if state & 0x80)

def to_name(key):
    return vk2name.get(key, None) or chr(key)

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_pressing_keys)
        self.timer.start(100)

    def paintEvent(self, ev):
        painter = QPainter(self)
        states = get_states()
        keys = get_keys(states)
        names = map(to_name, keys)
        painter.drawText(self.rect(), Qt.AlignCenter, str(names))

    def show_pressing_keys(self):
        states = get_states()
        print map(to_name, get_keys(states))
        self.update()

app = QApplication([])

font = app.font()
font.setFamily('Arial')
font.setPointSize(12)
app.setFont(font)

w = Widget()
w.show()
app.exec_()
