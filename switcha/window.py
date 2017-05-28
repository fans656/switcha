import locale

import win32gui
import win32con

from thumbnail import ThumbnailRender

__all__ = ['enum_windows', 'Windodws']

def enum_windows():
    hwnds = []
    win32gui.EnumWindows(lambda hwnd, _: hwnds.append(hwnd), None)
    return hwnds

def alt_tab_windows(hwnds=None):
    if hwnds is None:
        hwnds = enum_windows()
    return filter(is_alt_tab_window, hwnds)

def get_windows():
    wnds = map(Window, alt_tab_windows())
    wnds = filter(lambda w: w.title != 'Program Manager', wnds)
    return wnds

def is_alt_tab_window(hwnd):
    if not win32gui.IsWindowVisible(hwnd):
        return False
    if win32gui.GetParent(hwnd):
        return False
    if win32gui.GetWindow(hwnd, win32con.GW_OWNER):
        return False
    title = win32gui.GetWindowText(hwnd)
    if not title:
        return False
    return True

class Window(object):

    def __init__(self, hwnd=None):
        self._hwnd = hwnd

    @property
    def title(self):
        lang, encoding = locale.getdefaultlocale()
        return win32gui.GetWindowText(self._hwnd).decode(encoding)

    @property
    def current(self):
        return self._hwnd == win32gui.GetForegroundWindow()

    def __eq__(self, o):
        return self._hwnd == o._hwnd

    def __hash__(self):
        return hash(self._hwnd)

class DummyWindow(Window):

    def __init__(self):
        super(DummyWindow, self).__init__(None)

    @property
    def title(self):
        return u''

    @property
    def current(self):
        return False

    def __nonzero__(self):
        return False

class Windows(object):

    def __init__(self):
        self.wnds = get_windows()

    def update(self):
        old = self.wnds
        new = get_windows()
        wnds = [DummyWindow()] * max(len(old), len(new))
        for wnd in set(new) & set(old):
            wnds[old.index(wnd)] = wnd
        i = 0
        for wnd in set(new) - set(old):
            while wnds[i]:
                i += 1
            wnds[i] = wnd
        while not wnds[-1]:
            del wnds[-1]
        self.wnds = wnds

    def __iter__(self):
        return iter(self.wnds)

if __name__ == '__main__':
    wnds = map(Window, alt_tab_windows())
    for wnd in wnds:
        symbol = '*' if wnd.current else ' '
        print u'{} {}'.format(symbol, wnd.title)
#exit()
#
#class Window(object):
#
#    @staticmethod
#    def dummy(self):
#        return Window(hwnd=None, title=None, widget=None)
#
#    def __init__(self, hwnd, title, widget=None, wnds=None):
#        self.hwnd = hwnd
#        self.title = title
#        self.widget = widget
#        self.wnds = wnds
#        self.pinned = False
#
#        if widget:
#            self.thumbnail = ThumbnailRender(dst=widget, src=hwnd)
#            self.width = self.thumbnail.width
#            self.height = self.thumbnail.height
#
#    def activate(self):
#        hwnd = self.hwnd
#        _, showCmd, _, _, _ = win32gui.GetWindowPlacement(hwnd)
#        if showCmd == win32con.SW_SHOWMINIMIZED:
#            r = win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
#        else:
#            r = win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
#        r = win32gui.SetForegroundWindow(hwnd)
#        self.wnds.update()
#
#    @property
#    def current(self):
#        return self.hwnd == win32gui.GetForegroundWindow()
#
#    @property
#    def index(self):
#        return self.wnds.index(self)
#
#    def render(self, rc=None):
#        self.thumbnail.render(rc)
#
#    def __eq__(self, o):
#        return self.hwnd == o.hwnd
#
#    def __hash__(self):
#        return self.hwnd
#
#    def __repr__(self):
#        return repr(self.title[:8])
#
#class Windows(object):
#
#    def __init__(self, widget=None):
#        self.widget = widget
#        self.wnds = enum_windows(widget=widget, wnds=self)
#
#    def update(self):
#        old_wnds = self.wnds
#        new_wnds = enum_windows(widget=self.widget, wnds=self)
#        wnds = [None] * len(new_wnds)
#        for wnd in new_wnds:
#            if wnd in old_wnds:
#                i = next(i for i, w in enumerate(old_wnds)
#                         if wnd.hwnd == w.hwnd)
#                assert wnd.hwnd == old_wnds[i].hwnd
#                wnds[i] = wnd
#        i = 0
#        for wnd in new_wnds:
#            if wnd not in old_wnds:
#                while wnds[i]:
#                    i += 1
#                wnds[i] = wnd
#        self.wnds = wnds
#        #print 'old_wnds'
#        #print_wnds(old_wnds)
#        #print 'new_wnds'
#        #print_wnds(new_wnds)
#        #print wnds
#        #print [w.index for w in wnds]
#        #exit()
#
#    @property
#    def current(self):
#        if self.wnds:
#            return self.wnds[self.current_index]
#        else:
#            return Window.dummy()
#
#    @property
#    def next(self):
#        idx = (self.wnds.current_index - 1 + len(self.wnds)) % len(self.wnds)
#        return self.wnds[idx] if self.wnds else None
#
#    @property
#    def first(self):
#        return self.wnds[0] if self.wnds else None
#
#    @property
#    def last(self):
#        return self.wnds[0] if self.wnds else None
#
#    @property
#    def next(self):
#        return (self.wnds.current_index + 1) % len(self.wnds)
#
#    @property
#    def current_index(self):
#        cur = win32gui.GetForegroundWindow()
#        return next(i for i, wnd in enumerate(self.wnds) if wnd.hwnd == cur)
#
#    @property
#    def next(self):
#        return self[(self.current_index + 1) % len(self)]
#
#    @property
#    def prev(self):
#        return self[(self.current_index - 1 + len(self)) % len(self)]
#
#    def index(self, wnd):
#        try:
#            return self.wnds.index(wnd)
#        except ValueError:
#            return -1
#
#    def switch_to(self, idx, activate=True):
#        if not 0 <= idx < len(self):
#            return False
#        wnd = self.wnds[idx]
#        wnd.pinned = True
#        if activate:
#            wnd.activate()
#
#    def show(self):
#        print_wnds(self.wnds)
#        print
#
#    def __iter__(self):
#        return iter(self.wnds)
#
#    def __getitem__(self, i):
#        return self.wnds[i]
#
#    def __setitem__(self, i, o):
#        self.wnds[i] = o
#
#    def __len__(self):
#        return len(self.wnds)
#
#def print_wnds(wnds):
#    max_title_len = 40
#    for wnd in wnds:
#        try:
#            i = wnd.index
#            idx = '{:2}'.format(i + 1)
#            if wnd.pinned:
#                idx = '[{}]'.format(idx)
#            else:
#                idx = ' {} '.format(idx)
#            idx = '*{}'.format(idx) if wnd.current else ' {}'.format(idx)
#            title = (wnd.title[:max_title_len]
#                     + ('...' if len(wnd.title) > max_title_len else ''))
#            print '{} {:10} {}'.format(idx, wnd.hwnd, title)
#        except Exception:
#            print 'Unknown'
#
#if __name__ == '__main__':
#    wnds = Windows()
#    #wnds.switch_to(2 - 1)
#    #wnds.switch_to(4 - 1)
#    wnds.show()
