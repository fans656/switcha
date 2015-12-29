from PySide.QtCore import *
from PySide.QtGui import *
import pyHook
import win32con
import win32gui
import win32api
import win32process
import ctypes
from thumbnail import ThumbnailRender

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)

        self.hm = pyHook.HookManager()
        self.hm.KeyAll = self.on_key
        self.hm.HookKeyboard()

        self.wndlist = QListWidget()
        self.thumbnail = QWidget()
        self.thumbnail.setMinimumSize(QSize(700, 320))

        self.thumbnail_timer = QTimer()
        self.thumbnail_timer.timeout.connect(self.refresh)

        lt = QHBoxLayout()
        lt.addWidget(self.thumbnail)
        lt.addWidget(self.wndlist)
        self.setLayout(lt)

        self.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint)

    def on_key(self, ev):
        if ev.KeyID == win32con.VK_TAB:
            if ev.Alt:
                if ev.Message == win32con.WM_SYSKEYDOWN:
                    if not self.isVisible():
                        self.activate()
                    if pyHook.GetKeyState(win32con.VK_LSHIFT) or \
                            pyHook.GetKeyState(win32con.VK_RSHIFT):
                        self.on_alt_shift_tab_down()
                    else:
                        self.on_alt_tab_down()
                    return False
                elif ev.Message == win32con.WM_KEYUP:
                    self.on_alt_tab_up()
                    return False
        if ev.KeyID == win32con.VK_LMENU and ev.Message == win32con.WM_KEYUP:
            self.deactivate()
            # if return False here, the ALT key state is messed (but why?)
        if ev.Key.isdigit():
            self.select(int(ev.Key) - 1)
            self.deactivate()
        return True

    def on_alt_tab_down(self):
        row = self.wndlist.currentRow()
        row = (row + 1) % len(self.windows)
        self.select(row)

    def on_alt_shift_tab_down(self):
        row = self.wndlist.currentRow()
        row = (row + len(self.windows) - 1) % len(self.windows)
        self.select(row)

    def on_alt_tab_up(self):
        self.hide()

    def activate(self):
        self.windows = []
        win32gui.EnumWindows(self.filter_window, None)
        self.windows.pop() # remove Desktop window
        self.wndlist.clear()
        for i, (hwnd, title) in enumerate(self.windows):
            title = title.decode('gbk')
            text = '{} {}'.format(i + 1, title[:30])
            self.wndlist.addItem(text)
        self.select(0)
        self.show()
        self.thumbnail_timer.start(200)

    def select(self, index):
        self.wndlist.setCurrentRow(index)
        self.thumbnail_render = ThumbnailRender(
            # TODO: can't use non-toplevel window?
            dst=self,
            src=self.windows[index][0],
        )
        self.thumbnail_render.render()

    def refresh(self):
        self.thumbnail_render.render()

    def deactivate(self):
        if self.isVisible():
            self.thumbnail_timer.stop()
            self.hide()
            row = self.wndlist.currentRow()
            hwnd, title = self.windows[row]
            win32api.keybd_event(
                win32con.VK_LMENU, 0,
                win32con.KEYEVENTF_EXTENDEDKEY, 0
            )
            win32api.keybd_event(
                win32con.VK_LMENU, 0,
                win32con.KEYEVENTF_EXTENDEDKEY | win32con.KEYEVENTF_KEYUP, 0
            )
            if win32gui.IsIconic(hwnd):
                cmd_show = win32con.SW_RESTORE
            else:
                cmd_show = win32con.SW_SHOW
            win32gui.ShowWindow(hwnd, cmd_show)
            win32gui.SetForegroundWindow(hwnd)

    def filter_window(self, hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        if win32gui.GetParent(hwnd):
            return
        if win32gui.GetWindow(hwnd, win32con.GW_OWNER):
            return
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return
        self.windows.append((hwnd, title))

    def keyPressEvent(self, ev):
        print ev

app = QApplication([])
w = Widget()
#w.show()
app.exec_()
