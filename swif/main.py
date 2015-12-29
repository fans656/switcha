from PySide.QtCore import *
from PySide.QtGui import *
import pyHook
import win32con
import win32gui
import win32api
import win32process
import ctypes
from thumbnail import ThumbnailRender
from f6 import each

WIDTH_HEIGHT_RATIO = 1366.0 / 768
N_GRID = float(4)
COLOR_BASE = QColor('#DFE8EE')
COLOR_SELECTED = QColor('#616E75')
COLOR_SHORTCUT = QColor('#C6D4DC')
SHORTCUTS = 'ASDFQWER1234'

class Window(object):

    def __init__(self, hwnd, title, widget):
        self.hwnd = hwnd
        self.title = title.decode('gbk')
        self.thumbnail_render = ThumbnailRender(dst=widget, src=hwnd)

    def render(self):
        self.thumbnail_render.render(self.rc)

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)

        self.hm = pyHook.HookManager()
        self.hm.KeyAll = self.on_key
        self.hm.HookKeyboard()

        self.thumbnail_timer = QTimer()
        self.thumbnail_timer.timeout.connect(self.refresh)

        self.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint)

        self.cur_index = 0
        self.sticky = False
        self.simulating = False
        self.resize(QSize(1000, 600))

    def on_key(self, ev):
        # alt tab down
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
        if not self.isVisible():
            return True
        # alt tab up
        if ev.KeyID == win32con.VK_LMENU and ev.Message == win32con.WM_KEYUP \
                and not self.simulating:
            if self.sticky:
                self.sticky = False # sticky only once
            else:
                self.deactivate(lmenu_up=True)
            return False
        # switch by index
        elif ev.Key in SHORTCUTS:
            self.select(SHORTCUTS.index(ev.Key))
            self.deactivate()
            return False
        # stick the switcher '`'
        elif ev.Key == 'Oem_3' and ev.Message in (
            win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN):
            self.sticky = True
            return False
        # cancel
        elif ev.KeyID == win32con.VK_ESCAPE:
            self.deactivate(switch=False)
            return False
        return True

    def on_alt_tab_down(self):
        row = self.cur_index
        row = (row + 1) % len(self.windows)
        self.select(row)

    def on_alt_shift_tab_down(self):
        row = self.cur_index
        row = (row + len(self.windows) - 1) % len(self.windows)
        self.select(row)

    def on_alt_tab_up(self):
        self.hide()

    def activate(self):
        self.windows = []
        win32gui.EnumWindows(self.filter_window, None)
        self.windows.pop() # remove Desktop window
        (x_margin, y_margin,
         thumb_width, thumb_net_width,
         thumb_height, thumb_net_height) = self.get_geometries()
        for i, wnd in enumerate(self.windows):
            row, col = divmod(i, N_GRID)
            wnd.index = i
            wnd.rc = QRect(
                x_margin + col * thumb_width,
                y_margin + row * thumb_height,
                thumb_net_width,
                thumb_net_height)
        self.select(0)
        self.show()
        self.refresh()
        self.thumbnail_timer.start(200)
        QApplication.setActiveWindow(self)

    def select(self, index):
        self.cur_index = index
        wnd = self.windows[self.cur_index]
        self.refresh()

    def refresh(self):
        each(self.windows).render()
        self.update()

    def deactivate(self, lmenu_up=False, switch=True):
        if self.isVisible():
            self.thumbnail_timer.stop()
            self.hide()
            if not switch:
                return
            hwnd = self.windows[self.cur_index].hwnd
            # simulate system key event so SetForegroundWindow can succeed
            self.simulating = True
            # we need to keep the VK_LMENU up down state
            # so user needn't release alt to reactive the switcher
            # after a cancel
            #
            # during the process of WM_KEYUP event
            # pyHook.GetKeyState(win32con.VK_LMENU) will report it's still down
            # so we use lmenu_up variable here
            if lmenu_up:
                # down up
                win32api.keybd_event(
                    win32con.VK_LMENU, 0,
                    win32con.KEYEVENTF_EXTENDEDKEY, 0)
                win32api.keybd_event(
                    win32con.VK_LMENU, 0,
                    win32con.KEYEVENTF_EXTENDEDKEY | win32con.KEYEVENTF_KEYUP,
                    0)
            else:
                # up down
                win32api.keybd_event(
                    win32con.VK_LMENU, 0,
                    win32con.KEYEVENTF_EXTENDEDKEY | win32con.KEYEVENTF_KEYUP,
                    0)
                win32api.keybd_event(
                    win32con.VK_LMENU, 0,
                    win32con.KEYEVENTF_EXTENDEDKEY, 0)
            self.simulating = False
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
        self.windows.append(Window(hwnd, title, self))

    def get_geometries(self):
        rc_all = self.rect()
        x_margin = self.width() / 20.0
        y_margin = self.height() / 10.0
        thumb_width = (rc_all.width() - x_margin) / N_GRID
        thumb_height = thumb_width / WIDTH_HEIGHT_RATIO
        thumb_net_width = thumb_width - x_margin
        thumb_net_height = thumb_net_width / WIDTH_HEIGHT_RATIO
        return (x_margin, y_margin, thumb_width, thumb_net_width,
                thumb_height, thumb_net_height)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.fillRect(self.rect(), QBrush(COLOR_BASE))
        (x_margin, y_margin,
         thumb_width, thumb_net_width,
         thumb_height, thumb_net_height) = self.get_geometries()

        index = self.cur_index
        row, col = divmod(self.cur_index, N_GRID)
        offset = 10
        rc = QRect(
            x_margin + col * thumb_width - offset,
            y_margin + row * thumb_height - offset,
            thumb_net_width + offset * 2,
            thumb_net_height + offset * 2,
        )
        p.fillRect(rc, QBrush(COLOR_SELECTED))

        p.save()
        p.setPen(COLOR_SHORTCUT)
        for i, wnd in enumerate(self.windows):
            row, col = divmod(i, N_GRID)
            rc = QRect(
                x_margin + col * thumb_width + thumb_net_width,
                y_margin + row * thumb_height + thumb_net_height,
                x_margin / 2,
                y_margin / 2,
            )
            p.drawText(rc, Qt.AlignLeft | Qt.AlignTop, SHORTCUTS[i])
        p.restore()

        wnd = self.windows[self.cur_index]
        p.drawText(self.rect(), Qt.AlignHCenter | Qt.AlignBottom, wnd.title)

app = QApplication([])
font = app.font()
font.setFamily('Arial')
font.setPointSize(18)
app.setFont(font)
w = Widget()
app.exec_()
