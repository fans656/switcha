import ctypes


DWM_TNP_RECTDESTINATION = 0x00000001
DWM_TNP_RECTSOURCE = 0x00000002
DWM_TNP_OPACITY = 0x00000004
DWM_TNP_VISIBLE = 0x00000008
DWM_TNP_SOURCECLIENTAREAONLY = 0x00000010

dwmapi = ctypes.windll.dwmapi


class RECT(ctypes.Structure):

    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long),
    ]


class SIZE(ctypes.Structure):

    _fields_ = [
        ('cx', ctypes.c_long),
        ('cy', ctypes.c_long),
    ]


class ThumbProp(ctypes.Structure):

    _fields_ = [
        ('dwFlags', ctypes.c_long),
        ('rcDestination', RECT),
        ('rcSource', RECT),
        ('opacity', ctypes.c_byte),
        ('fVisible', ctypes.c_byte),
        ('fSourceClientAreaOnly', ctypes.c_byte),
    ]


class Thumb:

    def __init__(self, dst_hwnd, src_hwnd):
        '''
        Establish a relationship between image source window and
        destination window (as a drawing surface)
        '''
        self.dst_hwnd = dst_hwnd
        self.src_hwnd = src_hwnd
        self.handle = ctypes.c_long()
        dwmapi.DwmRegisterThumbnail(self.dst_hwnd, self.src_hwnd, ctypes.byref(self.handle))
        self._width = self._height = 0

    @property
    def width(self):
        self.update()
        return self._width

    @property
    def height(self):
        self.update()
        return self._height

    def update(self):
        size = SIZE()
        dwmapi.DwmQueryThumbnailSourceSize(self.handle, ctypes.byref(size))
        self._width, self._height = size.cx, size.cy

    def __del__(self):
        dwmapi.DwmUnregisterThumbnail(self.handle)

    def render(self, rect, pixel_ratio=1.0):
        thumbprop = ThumbProp()
        thumbprop.dwFlags = DWM_TNP_RECTDESTINATION | DWM_TNP_VISIBLE
        thumbprop.rcDestination.left = int(rect.left() * pixel_ratio)
        thumbprop.rcDestination.top = int(rect.top() * pixel_ratio)
        thumbprop.rcDestination.right = int(rect.right() * pixel_ratio)
        thumbprop.rcDestination.bottom = int(rect.bottom() * pixel_ratio)
        thumbprop.fSourceClientAreaOnly = 0
        thumbprop.fVisible = 1
        dwmapi.DwmUpdateThumbnailProperties(self.handle, ctypes.byref(thumbprop))
