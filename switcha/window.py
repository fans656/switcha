import locale
import logging
import ctypes
import struct
from ctypes import windll
from ctypes import wintypes
from functools import partial

import win32gui
import win32con
import win32api
import win32process
import pywintypes
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from f6 import each

try:
    from thumbnail import Thumbnail
    import config
except ImportError:
    pass

__all__ = [
    'enum_windows',
    'get_alt_tab_target',
    'Windodws',
    'RendableWindows',
]

user32 = windll.user32
gdi32 = windll.gdi32

ALT_TAB_EXCLUDES = set([
    r'C:\Windows\System32\ApplicationFrameHost.exe',
    r'C:\Windows\ImmersiveControlPanel\SystemSettings.exe',
    r'C:\Program Files\WindowsApps\Microsoft.Windows.Photos_17.425.10010.0_x64__8wekyb3d8bbwe\Microsoft.Photos.exe',
    r'C:\Program Files\WindowsApps\Microsoft.WindowsStore_11703.1001.45.0_x64__8wekyb3d8bbwe\WinStore.App.exe',
    r'C:\Windows\SystemApps\ShellExperienceHost_cw5n1h2txyewy\ShellExperienceHost.exe',
])

Normal = 0
Switched = 1
Pinned = 2

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
    wnds = filter(lambda w: w.path not in ALT_TAB_EXCLUDES, wnds)
    return wnds

def get_alt_tab_target():
    wnds = get_windows()
    return wnds[1] if wnds else None

def is_alt_tab_window(hwnd):
    if not win32gui.IsWindowVisible(hwnd):
        return False
    if win32gui.GetParent(hwnd):
        return False
    if win32gui.GetWindow(hwnd, win32con.GW_OWNER):
        return False
    if hwnd == windll.user32.GetShellWindow():
        return False
    title = win32gui.GetWindowText(hwnd)
    if (win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            & win32con.WS_EX_TOOLWINDOW):
        return False
    root = user32.GetAncestor(hwnd, win32con.GA_ROOTOWNER)
    last = last_visible_active_popup(root)
    if last != hwnd:
        return False
    if not title:
        return False
    return True

def last_visible_active_popup(hwnd):
    while True:
        h = user32.GetLastActivePopup(hwnd)
        if win32gui.IsWindowVisible(h):
            return h
        elif h == hwnd:
            return None
        hwnd = h

class Window(object):

    def __init__(self, hwnd, wnds, **kwargs):
        self.hwnd = hwnd
        self.wnds = wnds
        self.status = Normal
        self.hidden = False
        self._icon = None
        self.__dict__.update(**kwargs)

    def activate(self):
        logger.info(u'activate "{}"'.format(self.title))
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
        n = 512
        buf = ctypes.create_unicode_buffer(n)
        windll.user32.GetWindowTextW(self.hwnd, buf, n)
        return buf.value

    @property
    def active(self):
        return self.hwnd == win32gui.GetForegroundWindow()
    current = active

    @property
    def previously_active(self):
        return self is self.wnds.last_active

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

    @property
    def icon(self):
        if self._icon is None:
            self._icon = self.get_icon()
        return self._icon

    @property
    def path(self):
        tid, pid = win32process.GetWindowThreadProcessId(self.hwnd)
        try:
            access = (win32con.PROCESS_QUERY_INFORMATION
                      | win32con.PROCESS_VM_READ)
            handle = win32api.OpenProcess(access, False, pid)

            buf = ctypes.create_unicode_buffer(256)
            size = wintypes.DWORD(len(buf))
            windll.kernel32.QueryFullProcessImageNameW(
                int(handle), 0, ctypes.byref(buf), ctypes.pointer(size))
            path = buf.value
        except Exception as e:
            logger.warning('get exe path failed: hwnd={} title={}'.format(
                self.hwnd, repr(self.title)))
            return ''
        finally:
            try:
                win32api.CloseHandle(handle)
            except Exception:
                pass
        return path

    def get_icon(self):
        try:
            icons_large, icons_small = win32gui.ExtractIconEx(self.path, 0)
        except pywintypes.error:
            logger.warning('ExtractIconEx failed: title={}, path={}'.format(
                repr(self.title), self.path))
            return QPixmap()
        icons = icons_large + icons_small
        if not icons:
            logger.warning('no icons: {}'.format(self.path))
            return QPixmap()
        pixmap = hicon2pixmap(icons[0])
        for hicon in icons:
            win32gui.DestroyIcon(hicon)
        return pixmap

    def __eq__(self, o):
        return self.hwnd == o.hwnd

    def __hash__(self):
        return hash(self.hwnd)

class RendableWindow(Window):

    def __init__(self, wnd, target, *args, **kwargs):
        kwargs.update(wnd.__dict__)
        del kwargs['hwnd']
        super(RendableWindow, self).__init__(wnd.hwnd, *args, **kwargs)
        self.thumb = Thumbnail(target, wnd.hwnd)
        assert self.hidden == wnd.hidden

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

    @property
    def path(self):
        return ''

    def __nonzero__(self):
        return False

class Windows(object):

    def __init__(self):
        self.wnds = get_windows(self)
        self.enable_hidden = True

    def toggle_hidden(self):
        self.enable_hidden = not self.enable_hidden
        self.update()

    def update(self):
        old = self.wnds
        new = get_windows(self)
        wnds = [DummyWindow(wnds=self)
                for _ in xrange(max(len(old), len(new)))]
        if self.enable_hidden:
            for should_hide in config.should_hides:
                new = filter(lambda w: not should_hide(w), new)
        # group similar windows
        new.sort(key=lambda w: w.path)
        # stick old windows
        for wnd in set(new) & set(old):
            idx = old.index(wnd)
            # use old wnd (reuse resources like icon etc)
            wnds[idx] = old[idx]
        # flow new windows
        i = 0
        for wnd in set(new) - set(old):
            while wnds[i]:
                i += 1
            wnds[i] = wnd
        # fill middle holes
        for i in xrange(0, len(wnds)):
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
        return next((i for i, w in enumerate(self.wnds) if w.current), -1)

    @property
    def current(self):
        return next((w for w in self.wnds if w.current), None)

    @property
    def has_current(self):
        return self.current_index != -1

    @property
    def first(self):
        return next(w for w in self.wnds if w)

    @property
    def last_active(self):
        wnds = get_windows()
        if not wnds:
            return None
        elif len(wnds) == 1:
            return None
        else:
            prev_active = wnds[1]
            return next((w for w in self.wnds if w.hwnd == prev_active.hwnd),
                        None)

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

    @property
    def alt_tab_target(self):
        return get_alt_tab_target()

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

    def __contains__(self, wnd):
        return wnd in self.wnds

    def __nonzero__(self):
        return any(w for w in self.wnds)

class RendableWindows(Windows):

    def __init__(self, target):
        """Create a windows manager support rendering

        Args:
            target - a QWidget target to render thumbnails to
        """
        super(RendableWindows, self).__init__()
        self.wnds = [RendableWindow(wnd, target, wnds=self)
                     for wnd in self.wnds]
        self.target = target
        wnds = self.wnds
        if len(wnds) < 8:
            main, other = wnds[:4], wnds[4:]
            padding = [DummyWindow(wnds=self) for _ in xrange(4 - len(other))]
            self.wnds = other + padding + main

    def update(self):
        super(RendableWindows, self).update()
        wnds = self.wnds
        if len(wnds) < 8:
            dummies = [DummyWindow(wnds=self) for _ in xrange(8 - len(wnds))]
        for i, wnd in enumerate(wnds):
            if not wnd or isinstance(wnd, RendableWindow):
                continue
            wnds[i] = RendableWindow(wnd, self.target, wnds=self)

# convert hIcon to QPixmap
# https://evilcodecave.wordpress.com/2009/08/03/qt-undocumented-from-hicon-to-qpixmap/

class ICONINFO(ctypes.Structure):

    _fields_ = [
        ('fIcon', wintypes.BOOL),
        ('xHotspot', wintypes.DWORD),
        ('yHotspot', wintypes.DWORD),
        ('hbmMask', wintypes.HBITMAP),
        ('hbmColor', wintypes.HBITMAP),
    ]

class RGBQUAD(ctypes.Structure):

    _fields_ = [
        ('rgbBlue', wintypes.BYTE),
        ('rgbGreen', wintypes.BYTE),
        ('rgbRed', wintypes.BYTE),
        ('rgbReserved', wintypes.BYTE),
    ]

class BITMAPINFOHEADER(ctypes.Structure):

    _fields_ = [
        ('biSize', wintypes.DWORD),
        ('biWidth', wintypes.LONG),
        ('biHeight', wintypes.LONG),
        ('biPlanes', wintypes.WORD),
        ('biBitCount', wintypes.WORD),
        ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD),
        ('biXPelsPerMeter', wintypes.LONG),
        ('biYPelsPerMeter', wintypes.LONG),
        ('biClrUsed', wintypes.DWORD),
        ('biClrImportant', wintypes.DWORD),
    ]

class BITMAPINFO(ctypes.Structure):

    _fields_ = [
        ('bmiHeader', BITMAPINFOHEADER),
        ('bmiColors', RGBQUAD),
    ]

def hicon2pixmap(icon):
    screen = user32.GetDC(0)
    hdc = gdi32.CreateCompatibleDC(screen)
    user32.ReleaseDC(0, screen)

    iconinfo = ICONINFO()
    if not user32.GetIconInfo(icon, ctypes.byref(iconinfo)):
        logger.warning('convert hIcon to QPixmap failed')
        return QPixmap()
    w = iconinfo.xHotspot * 2
    h = iconinfo.yHotspot * 2

    bitmapInfo = BITMAPINFOHEADER()
    bitmapInfo.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bitmapInfo.biWidth = w
    bitmapInfo.biHeight = h
    bitmapInfo.biPlanes = 1
    bitmapInfo.biBitCount = 32
    bitmapInfo.biCompression = win32con.BI_RGB
    bitmapInfo.biSizeImage = 0
    bitmapInfo.biXPelsPerMeter = 0
    bitmapInfo.biYPelsPerMeter = 0
    bitmapInfo.biClrUsed = 0
    bitmapInfo.biClrImportant = 0

    bits = ctypes.POINTER(wintypes.DWORD)()
    winBitmap = gdi32.CreateDIBSection(
        hdc,
        ctypes.byref(bitmapInfo),
        win32con.DIB_RGB_COLORS,
        ctypes.byref(bits),
        0, 0)
    oldhdc = gdi32.SelectObject(hdc, winBitmap)
    user32.DrawIconEx(hdc, 0, 0, icon,
                      iconinfo.xHotspot * 2, iconinfo.yHotspot * 2,
                      0, 0, win32con.DI_NORMAL)
    image = from_hbitmap(hdc, winBitmap, w, h)
    foundAlpha = False
    for y in xrange(h):
        scanLine = image.scanLine(y)
        scanLine.setsize(w * 4)
        for x in xrange(w):
            i = x * 4
            rgb, = struct.unpack_from('=I', scanLine, i)
            if qAlpha(rgb):
                foundAlpha = True
        if foundAlpha:
            break
    if not foundAlpha:
        user32.DrawIconEx(hdc, 0, 0, icon, w, h, 0, 0, win32con.DI_MASK)
        mask = from_hbitmap(hdc, winBitmap, w, h)
        for y in xrange(h):
            scanLineImage = image.scanLine(y)
            scanLineImage.setsize(w * 4)
            scanLineMask = 0 if mask.isNull() else mask.scanLine(y)
            scanLineMask.setsize(w * 4)
            for x in xrange(w):
                i = x * 4
                mask_val = struct.unpack('=I', scanLineMask[i:i+4])[0]
                if scanLineMask and qRed(mask_val):
                    scanLineImage[i:i+4] = struct.pack('=I', 0)
                else:
                    img_val = struct.unpack('=I', scanLineImage[i:i+4])[0]
                    img_val |= 0xff000000
                    scanLineImage[i:i+4] = struct.pack('=I', img_val)
    gdi32.DeleteObject(iconinfo.hbmMask)
    gdi32.DeleteObject(iconinfo.hbmMask)
    gdi32.SelectObject(hdc, oldhdc)
    gdi32.DeleteObject(winBitmap)
    gdi32.DeleteDC(hdc)
    return QPixmap.fromImage(image)

def from_hbitmap(hdc, hbitmap, w, h):
    bmi = BITMAPINFO()
    ctypes.memset(ctypes.byref(bmi), 0, ctypes.sizeof(bmi))
    bmi.bmiHeader.biSize        = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth       = w
    bmi.bmiHeader.biHeight      = -h
    bmi.bmiHeader.biPlanes      = 1
    bmi.bmiHeader.biBitCount    = 32
    bmi.bmiHeader.biCompression = win32con.BI_RGB
    bmi.bmiHeader.biSizeImage   = w * h * 4

    image = QImage(w, h, QImage.Format_ARGB32_Premultiplied)

    data = ctypes.create_string_buffer(bmi.bmiHeader.biSizeImage)
    memcpy = ctypes.cdll.msvcrt.memcpy
    if gdi32.GetDIBits(hdc, hbitmap, 0, h, data, ctypes.byref(bmi),
                       win32con.DIB_RGB_COLORS):
        for y in xrange(h):
            dest = image.scanLine(y)
            dest.setsize(w * 4)
            bpl = image.bytesPerLine()
            i = y * bpl
            dest[:] = data[i:i+bpl]
    else:
        logger.warning(
            'converting hIcon to QPixmap, failed to get bitmap bits')
    return image

if __name__ == '__main__':
    wnds = Windows()
    wnds.update()
    for wnd in wnds:
        print wnd.title
        print repr(wnd.path), config.should_hides[0](wnd)
        print
