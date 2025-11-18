import ctypes
from ctypes import windll
from ctypes import wintypes
import functools

import win32gui
import win32con
import win32api
import win32process

from switcha import utils
from switcha.qt import *
from switcha.icon import icon_from_path
from switcha.thumb import Thumb
from switcha.conf import ALT_TAB_EXCLUDES_PATTERN


user32 = windll.user32
kernel32 = windll.kernel32


class Windows(list):

    def __init__(self, surface_hwnd=None):
        self._surface_hwnd = surface_hwnd
        self._hwnds = set()
        self.update()

    @property
    def current_window(self):
        foreground_hwnd = win32gui.GetForegroundWindow()
        return next((w for w in self if w.hwnd == foreground_hwnd), None)

    def update(self):
        self._hwnds = _get_interested_hwnds()
        utils.sync(self, self._hwnds, create=self._create_window, key=lambda w: w.hwnd)
        return self

    def _create_window(self, hwnd):
        window = Window(hwnd)
        if self._surface_hwnd:
            window.create_thumb(self._surface_hwnd)
        return window


class Window:

    def __init__(self, hwnd):
        self.hwnd = hwnd
        self.thumb = None

    @property
    def title(self):
        return _title_from_hwnd(self.hwnd)

    @functools.cached_property
    def path(self):
        return _path_from_hwnd(self.hwnd)

    @functools.cached_property
    def icon(self) -> QPixmap:
        return icon_from_path(self.path)

    def create_thumb(self, surface_hwnd):
        self.thumb = Thumb(surface_hwnd, self.hwnd)

    def activate(self):
        _activate_hwnd(self.hwnd)

    def __hash__(self):
        return hash(self.hwnd)

    def __eq__(self, other):
        return other and self.hwnd == other.hwnd

    def __del__(self):
        pass

    def __repr__(self):
        return f'Window(title="{self.title}", hwnd={self.hwnd})'


def _get_interested_hwnds() -> set[int]:
    return {hwnd for hwnd in _get_hwnds() if _is_interested_hwnd(hwnd)}


def _get_hwnds() -> set[int]:
    hwnds = set()
    win32gui.EnumWindows(lambda hwnd, _: hwnds.add(hwnd), None)
    return hwnds


def _is_interested_hwnd(hwnd: int) -> bool:
    if not win32gui.IsWindowVisible(hwnd):
        return False  # not visible

    if win32gui.GetParent(hwnd):
        return False  # not root window

    if win32gui.IsIconic(hwnd):
        return False  # trayed

    if hwnd == user32.GetShellWindow():
        return False

    style_ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

    has_owner = win32gui.GetWindow(hwnd, win32con.GW_OWNER) != 0
    is_appwindow = style_ex & win32con.WS_EX_APPWINDOW
    if has_owner and not is_appwindow:
        return False

    if style_ex & win32con.WS_EX_TOOLWINDOW:
        return False  # tool window

    if ALT_TAB_EXCLUDES_PATTERN.match(_path_from_hwnd(hwnd)):
        return False

    if not _title_from_hwnd(hwnd):
        return False

    return True


def _path_from_hwnd(hwnd):
    tid, pid = win32process.GetWindowThreadProcessId(hwnd)
    access = win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ
    handle = win32api.OpenProcess(access, False, pid)

    try:
        buf = ctypes.create_unicode_buffer(256)
        size = wintypes.DWORD(len(buf))
        kernel32.QueryFullProcessImageNameW(
            int(handle),
            0,
            ctypes.byref(buf),
            ctypes.pointer(size),
        )
        return buf.value
    finally:
        win32api.CloseHandle(handle)


def _title_from_hwnd(hwnd):
    n = 512
    buf = ctypes.create_unicode_buffer(n)
    user32.GetWindowTextW(hwnd, buf, n)
    return buf.value


def _activate_hwnd(hwnd):
    win32gui.ShowWindow(hwnd, _show_cmd_from_hwnd(hwnd))
    win32gui.SetForegroundWindow(hwnd)


def _show_cmd_from_hwnd(hwnd):
    show_state = _show_state_from_hwnd(hwnd)
    if show_state == win32con.SW_SHOWMINIMIZED:
        return win32con.SW_RESTORE
    else:
        return win32con.SW_SHOW


def _show_state_from_hwnd(hwnd):
    """
    Returns:
        show state one of SW_* contants.

        https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow
    """
    _, show_state, _, _, _ = win32gui.GetWindowPlacement(hwnd)
    return show_state


if __name__ == '__main__':
    app = QApplication([])
    for wnd in Windows():
        print(wnd)
        print(wnd.icon)
