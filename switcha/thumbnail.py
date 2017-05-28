from PySide.QtCore import *
from PySide.QtGui import *
import ctypes
import win32gui

__all__ = ['Thumbnail']

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

class Thumbnail(object):

    def __init__(self, dst, src):
        '''
        dst - QWidget
        src - hwnd

        Establish a relationship between image source window and
        destination window (as a drawing surface)
        '''
        self.dst = dst
        self.src = src
        self.thumbnail = ctypes.c_long()
        dwmapi.DwmRegisterThumbnail(
            int(self.dst.winId()), self.src, ctypes.byref(self.thumbnail))
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
        sz = SIZE()
        dwmapi.DwmQueryThumbnailSourceSize(self.thumbnail, ctypes.byref(sz))
        self._width, self._height = sz.cx, sz.cy

    def __del__(self):
        dwmapi.DwmUnregisterThumbnail(self.thumbnail)

    def render(self, rc=None):
        '''
        Do the actual drawing

        rc - QRect in destination's coordinate
        '''
        thumbprop = ThumbProp()
        thumbprop.dwFlags = (
            DWM_TNP_RECTDESTINATION |
            DWM_TNP_VISIBLE |
            DWM_TNP_SOURCECLIENTAREAONLY
        )
        if rc is None:
            rc = self.dst.rect()
        thumbprop.rcDestination.left = rc.left()
        thumbprop.rcDestination.top = rc.top()
        thumbprop.rcDestination.right = rc.right()
        thumbprop.rcDestination.bottom = rc.bottom()
        thumbprop.fSourceClientAreaOnly = 0
        thumbprop.fVisible = 1
        thumbprop.fSourceClientAreaOnly = 1
        dwmapi.DwmUpdateThumbnailProperties(
            self.thumbnail, ctypes.byref(thumbprop))
