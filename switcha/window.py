import win32gui
import win32con

from thumbnail import ThumbnailRender

__all__ = ['enum_windows', 'Windodws']

def enum_windows(pred=None, widget=None, windows=None):

    def collect(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if pred(hwnd, title):
            wnds.append(Window(hwnd=hwnd, title=title, widget=widget,
                               windows=windows))

    if pred is None:
        pred = is_alt_tab_window
    wnds = []
    win32gui.EnumWindows(collect, None)
    return wnds

def current_window(wnds):
    cur_hwnd = win32gui.GetForegroundWindow()
    return next((wnd for wnd in wnds if wnd.hwnd == cur_hwnd),
                Window(None, 'dummy'))

class Window(object):

    @staticmethod
    def dummy(self):
        return Window(hwnd=None, title=None, widget=None)

    def __init__(self, hwnd, title, widget=None, windows=None):
        self.hwnd = hwnd
        self.title = title
        self.widget = widget
        self.windows = windows
        self.pinned = False

        if widget:
            self.thumbnail = ThumbnailRender(dst=widget, src=hwnd)
            self.width = self.thumbnail.width
            self.height = self.thumbnail.height

    def activate(self):
        hwnd = self.hwnd
        _, showCmd, _, _, _ = win32gui.GetWindowPlacement(hwnd)
        if showCmd == win32con.SW_SHOWMINIMIZED:
            r = win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        else:
            r = win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        r = win32gui.SetForegroundWindow(hwnd)

    @property
    def current(self):
        return self.hwnd == win32gui.GetForegroundWindow()

    def render(self, rc=None):
        self.thumbnail.render(rc)

    def __eq__(self, o):
        return self.hwnd == o.hwnd

    def __hash__(self):
        return self.hwnd

class Windows(object):

    def __init__(self, widget=None):
        self.widget = widget
        self.wnds = enum_windows(widget=widget, windows=self)

    def update(self):
        wnds = enum_windows(self.widget)

    @property
    def current(self):
        if self.wnds:
            return self.wnds[self.current_index]
        else:
            return Window.dummy()

    @property
    def next(self):
        idx = (self.wnds.current_index - 1 + len(self.wnds)) % len(self.wnds)
        return self.wnds[idx] if self.wnds else None

    @property
    def first(self):
        return self.wnds[0] if self.wnds else None

    @property
    def last(self):
        return self.wnds[0] if self.wnds else None

    @property
    def next(self):
        return (self.wnds.current_index + 1) % len(self.wnds)

    @property
    def current_index(self):
        cur = win32gui.GetForegroundWindow()
        return next(i for i, wnd in enumerate(self.wnds) if wnd.hwnd == cur)

    @property
    def next(self):
        return self[(self.current_index + 1) % len(self)]

    @property
    def prev(self):
        return self[(self.current_index - 1 + len(self)) % len(self)]

    def index(self, wnd):
        try:
            return self.wnds.index(wnd)
        except ValueError:
            return -1

    def switch_to(self, idx, activate=True):
        if not 0 <= idx < len(self):
            return False
        wnd = self.wnds[idx]
        wnd.pinned = True
        if activate:
            wnd.activate()

    def show(self):
        print_wnds(self.wnds)
        print

    def __iter__(self):
        return iter(self.wnds)

    def __getitem__(self, i):
        return self.wnds[i]

    def __setitem__(self, i, o):
        self.wnds[i] = o

    def __len__(self):
        return len(self.wnds)

def is_alt_tab_window(hwnd, title):
    if not win32gui.IsWindowVisible(hwnd):
        return False
    if win32gui.GetParent(hwnd):
        return False
    if win32gui.GetWindow(hwnd, win32con.GW_OWNER):
        return False
    if not title:
        return False
    if title == 'Program Manager':  # exclude the desktop, use win+d
        return False
    return True

def print_wnds(wnds):
    max_title_len = 40
    for i, wnd in enumerate(wnds):
        try:
            idx = '{:2}'.format(i + 1)
            if wnd.pinned:
                idx = '[{}]'.format(idx)
            else:
                idx = ' {} '.format(idx)
            idx = '*{}'.format(idx) if wnd.current else ' {}'.format(idx)
            title = (wnd.title[:max_title_len]
                     + ('...' if len(wnd.title) > max_title_len else ''))
            print '{} {:10} {}'.format(idx, wnd.hwnd, title)
        except Exception:
            print 'Unknown'

if __name__ == '__main__':
    wnds = Windows()
    wnds.switch_to(2 - 1)
    wnds.switch_to(4 - 1)
    wnds.show()
