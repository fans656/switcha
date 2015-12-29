from PySide.QtCore import *
from PySide.QtGui import *
import ctypes
import win32gui

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

class ThumbProp(ctypes.Structure):

    _fields_ = [
        ('dwFlags', ctypes.c_long),
        ('rcDestination', RECT),
        ('rcSource', RECT),
        ('opacity', ctypes.c_byte),
        ('fVisible', ctypes.c_byte),
        ('fSourceClientAreaOnly', ctypes.c_byte),
    ]

def get_hwnd(widget):
    pycobject_hwnd = widget.winId()
    ctypes.pythonapi.PyCObject_AsVoidPtr.restype = ctypes.c_void_p
    ctypes.pythonapi.PyCObject_AsVoidPtr.argtypes = [ctypes.py_object]
    hwnd = ctypes.pythonapi.PyCObject_AsVoidPtr(pycobject_hwnd)
    return hwnd

class ThumbnailRender(object):

    def __init__(self, dst, src):
        self.dst = dst
        self.src = src
        self.thumbnail = ctypes.c_long()
        dwmapi.DwmRegisterThumbnail(
            get_hwnd(self.dst), self.src, ctypes.byref(self.thumbnail))
        print 'register', win32gui.GetWindowText(self.src)

    def __del__(self):
        dwmapi.DwmUnregisterThumbnail(self.thumbnail)
        print 'unregister', win32gui.GetWindowText(self.src)

    def render(self, rc=None):
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
        dwmapi.DwmUpdateThumbnailProperties(
            self.thumbnail, ctypes.byref(thumbprop))
        #print 'render', win32gui.GetWindowText(self.src)
