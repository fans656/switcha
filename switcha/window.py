import win32gui
import win32con

from thumbnail import ThumbnailRender

__all__ = ['enum_windows', 'Windodws']

def enum_windows(pred=None, widget=None):

    def collect(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if pred(hwnd, title):
            wnds.append(Window(hwnd=hwnd, title=title, widget=widget))

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

    def __init__(self, hwnd, title, widget=None):
        self.hwnd = hwnd
        self.title = title
        self.widget = widget

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
        #r = win32gui.BringWindowToTop(hwnd)
        r = win32gui.SetForegroundWindow(hwnd)
        #r = win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0,0,0,0,
        #                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        #print 'SetWindowPos HWND_NOTOPMOST', r
        #r = win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0,0,0,0,
        #                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        #print 'SetWindowPos HWND_TOPMOST', r
        #r = win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0,0,0,0,
        #                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        #print 'SetWindowPos HWND_NOTOPMOST', r

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
        self.wnds = []
        self.update(widget)

    def update(self, widget=None):
        old_wnds = self.wnds
        new_wnds = enum_windows(widget=widget or self.widget)

        wnd2idx = {wnd: i for i, wnd in enumerate(old_wnds)}
        wnds = [None] * len(new_wnds)
        i = 0
        for wnd in new_wnds:
            idx = wnd2idx.get(wnd, None)
            if idx:
                wnds[idx] = wnd
                #print 'Found "{}", {}'.format(wnd.title, idx)
            else:
                while wnds[i]:
                    i += 1
                wnds[i] = wnd
                #print 'New "{}", {}'.format(wnd.title, i)
                i += 1
        #banner = '=' * 40
        #print banner, 'old windows:'
        #print_wnds(old_wnds)
        #print banner, 'new windows:'
        #print_wnds(wnds)
        self.wnds = wnds

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
    #print '*' * 40
    #for wnd in wnds:
    #    print wnd
    #print '*' * 40
    for i, wnd in enumerate(wnds):
        idx = '{:2}'.format(i + 1)
        idx = '[{}]'.format(idx) if wnd.current else ' {} '.format(idx)
        title = repr(wnd.title)
        print '{} {:10} {}'.format(idx, wnd.hwnd, title)

if __name__ == '__main__':
    wnds = Windows()
