import locale
import logging
from functools import partial

import win32gui
import win32con
from f6 import each

try:
    from thumbnail import Thumbnail
except ImportError:
    pass

__all__ = ['enum_windows', 'Windodws', 'RendableWindows']

Normal = 0
Switched = 1
Pinned = 2

logger = logging.getLogger(__name__)

def enum_windows():
    hwnds = []
    win32gui.EnumWindows(lambda hwnd, _: hwnds.append(hwnd), None)
    return hwnds

def alt_tab_windows(hwnds=None):
    if hwnds is None:
        hwnds = enum_windows()
    return filter(is_alt_tab_window, hwnds)

def get_windows(wnds=None):
    wnds = [Window(hwnd, wnds=wnds) for hwnd in alt_tab_windows()]
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

    def __init__(self, hwnd, wnds):
        self.hwnd = hwnd
        self.wnds = wnds
        self.status = Normal

    def activate(self):
        hwnd = self.hwnd
        _, showCmd, _, _, _ = win32gui.GetWindowPlacement(hwnd)
        minimized = showCmd == win32con.SW_SHOWMINIMIZED
        cmdShow = win32con.SW_RESTORE if minimized else win32con.SW_SHOW
        win32gui.ShowWindow(hwnd, cmdShow)
        win32gui.SetForegroundWindow(hwnd)
        self.status = max(Switched, self.status)

    def pin_to(self, i):
        if i < 0:
            logger.warning('{} pin to {}?'.format(self.index, i))
            return False
        logger.info('{} pin to {}'.format(self.index, i))
        wnds = self.wnds
        if i >= len(wnds):
            wnds.extend([DummyWindow(wnds=self.wnds)
                         for _ in xrange(i + 1 - len(wnds))])
        j = self.index
        logger.debug('target: {}, source: {}'.format(i, j))
        wnds[i], wnds[j] = wnds[j], wnds[i]
        self.status = Pinned
        return True

    @property
    def title(self):
        lang, encoding = locale.getdefaultlocale()
        return win32gui.GetWindowText(self.hwnd).decode(encoding)

    @property
    def current(self):
        return self.hwnd == win32gui.GetForegroundWindow()

    @property
    def index(self):
        return self.wnds.index(self)

    @property
    def pinned(self):
        return self.status == Pinned

    @property
    def switched(self):
        return self.status == Switched

    @property
    def normal(self):
        return self.status == Normal

    def __eq__(self, o):
        return self.hwnd == o.hwnd

    def __hash__(self):
        return hash(self.hwnd)

class RendableWindow(Window):

    def __init__(self, hwnd, target, *args, **kwds):
        assert 'wnds' in kwds
        super(RendableWindow, self).__init__(hwnd, *args, **kwds)
        self.thumb = Thumbnail(target, hwnd)

    def render(self, rc):
        self.thumb.render(rc)

    @property
    def width(self):
        return self.thumb.width

    @property
    def height(self):
        return self.thumb.height

class DummyWindow(Window):

    def __init__(self, *args, **kwds):
        super(DummyWindow, self).__init__(hwnd=None, *args, **kwds)

    @property
    def title(self):
        return u''

    @property
    def current(self):
        return False

    @property
    def index(self):
        # Window.__eq__ is based on `hwnd`
        # DummyWindow's `hwnd` is always `None`
        # rewrite to get the right index in case of mutiple dummies
        return next(i for i, w in enumerate(self.wnds) if w is self)

    def __nonzero__(self):
        return False

class Windows(object):

    def __init__(self):
        self.wnds = get_windows(self)

    def update(self):
        old = self.wnds
        new = get_windows(self)
        wnds = [DummyWindow(wnds=self)
                for _ in xrange(max(len(old), len(new)))]
        # stick old windows
        for wnd in set(new) & set(old):
            idx = old.index(wnd)
            wnds[idx] = old[idx]
        # flow new windows
        i = 0
        for wnd in set(new) - set(old):
            while wnds[i]:
                i += 1
            wnds[i] = wnd
        # fill middle holes
        for i in xrange(4, len(wnds)):
            wnd = wnds[i]
            if wnd:
                continue
            j = next((j for j in xrange(i + 1, len(wnds))
                     if wnds[j] and wnds[j].normal), None)
            if j is None:
                break
            wnds[i], wnds[j] = wnds[j], wnds[i]
        # trim tail holes
        while not wnds[-1]:
            del wnds[-1]
        self.wnds = wnds

    @property
    def current_index(self):
        return

    @property
    def current(self):
        return next((w for w in self.wnds if w.current), None)

    @property
    def has_current(self):
        return self.current_index != -1

    @property
    def next(self):
        i = self.current_index
        while True:
            i = (i + 1) % len(self)
            wnd = self[i]
            if wnd:
                return wnd

    @property
    def prev(self):
        i = self.current_index
        while True:
            i = (i - 1 + len(self)) % len(self)
            wnd = self[i]
            if wnd:
                return wnd

    def index(self, wnd):
        return self.wnds.index(wnd)

    def extend(self, a):
        self.wnds.extend(a)

    def __len__(self):
        return len(self.wnds)

    def __iter__(self):
        return iter(self.wnds)

    def __getitem__(self, i):
        return self.wnds[i]

    def __setitem__(self, i, v):
        self.wnds[i] = v

class RendableWindows(Windows):

    def __init__(self, target):
        """Create a windows manager support rendering

        Args:
            target - a QWidget target to render thumbnails to
        """
        super(RendableWindows, self).__init__()
        assert all(not isinstance(w, DummyWindow) for w in self.wnds)
        self.wnds = [RendableWindow(w.hwnd, target, wnds=self)
                     for w in self.wnds]
        self.target = target
        wnds = self.wnds
        if len(wnds) < 8:
            main, other = wnds[:4], wnds[4:]
            padding = [DummyWindow(wnds=self) for _ in xrange(4 - len(other))]
            self.wnds = other + padding + main

    def update(self):
        super(RendableWindows, self).update()
        wnds = self.wnds
        for i, wnd in enumerate(wnds):
            if not wnd or isinstance(wnd, RendableWindow):
                continue
            wnds[i] = RendableWindow(wnd.hwnd, self.target, wnds=self)
        assert all(w.wnds for w in self.wnds)
