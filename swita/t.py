import win32gui
import win32api
import win32con

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from f6.pyside import gethwnd

from window import Windows

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        hwnd = self.winId()
        win32gui.RegisterHotKey(
            hwnd, 0,
            win32con.MOD_CONTROL | win32con.MOD_ALT, ord('F'))
        win32gui.RegisterHotKey(
            hwnd, 1,
            win32con.MOD_CONTROL | win32con.MOD_ALT, ord('2'))

    def winEvent(self, msg):
        if msg.message == win32con.WM_HOTKEY:
            print msg.wParam
            wnds = Windows()
            wnd = next(w for w in wnds if w.title == 'swita')
            hwnd = wnd.hwnd
            print wnd.title
            #win32gui.BringWindowToTop(hwnd)
            #win32gui.SetForegroundWindow(hwnd)
            _, showCmd, _, _, _ = win32gui.GetWindowPlacement(hwnd)
            if showCmd == win32con.SW_SHOWMINIMIZED:
                r = win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                print 'ShowWindow', r
            else:
                r = win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                print 'ShowWindow', r
            r = win32gui.BringWindowToTop(hwnd)
            print 'BringWindowToTop', r
            r = win32gui.SetForegroundWindow(hwnd)
            print 'SetForegroundWindow', r
            r = win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0,0,0,0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            print 'SetWindowPos HWND_NOTOPMOST', r
            r = win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0,0,0,0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            print 'SetWindowPos HWND_TOPMOST', r
            r = win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0,0,0,0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            print 'SetWindowPos HWND_NOTOPMOST', r
            return True, 0
        return False, 0

app = QApplication([])
w = Widget()
#w.show()
app.exec_()
