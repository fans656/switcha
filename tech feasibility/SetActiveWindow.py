'''
https://msdn.microsoft.com/en-us/library/windows/desktop/ms646311(v=vs.85).aspx

you can only make your thread's window active
and when your thread is foreground,
otherwise you will fail
'''
from PySide.QtCore import *
from PySide.QtGui import *
import pyHook
import win32gui
import win32api
from f6.pyside import widget2hwnd
from f6.win32 import task_windows

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)

def on_key(ev):
    if ev.Key == '1':
        hwnd = widget2hwnd(w)
    elif ev.Key == '2':
        hwnd = widget2hwnd(w2)
    elif ev.Key == '3':
        hwnd, _ = task_windows()[-1]
    else:
        return True
    r = win32gui.SetActiveWindow(hwnd)
    if not r:
        print 'error', win32api.GetLastError()
    return False

hm = pyHook.HookManager()
hm.KeyDown = on_key
hm.HookKeyboard()

app = QApplication([])
w = Widget()
w.setWindowTitle('1')
w.show()
w2 = Widget()
w2.setWindowTitle('2')
w2.show()
w2.move(300, 300)
app.exec_()
