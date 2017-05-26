from PySide.QtCore import *
from PySide.QtGui import *
import pyHook
import win32api
import win32con

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)

def on_key(ev):
    key = win32con.VK_LMENU
    #key = ord('1')
    if ev.KeyID == key:
        print 'intercept', ev.Key, 'down' if ev.Message in (win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN) else 'up'
        return False
    elif ev.Key == '2':
        if ev.Message == win32con.WM_KEYDOWN:
            win32api.keybd_event(key, 0, 0, 0)
            #win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)
        return False
    else:
        return True

hm = pyHook.HookManager()
hm.KeyAll = on_key
hm.HookKeyboard()

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)

    def keyPressEvent(self, ev):
        print ev, 'down'
        super(Widget, self).keyPressEvent(ev)

    def keyReleaseEvent(self, ev):
        print ev, 'up'
        super(Widget, self).keyReleaseEvent(ev)

app = QApplication([])
w = Widget()
#w.show()
app.exec_()
