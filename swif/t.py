from PySide.QtCore import *
from PySide.QtGui import *
import ctypes
import win32gui

DWM_TNP_RECTDESTINATION = 0x00000001
DWM_TNP_RECTSOURCE = 0x00000002
DWM_TNP_OPACITY = 0x00000004
DWM_TNP_VISIBLE = 0x00000008
DWM_TNP_SOURCECLIENTAREAONLY = 0x00000010

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

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        desktop = win32gui.FindWindow('Progman', None)
        #desktop = win32gui.FindWindow(None, '192.168.128.130 - Putty')

        pycobject_hwnd = self.winId()
        ctypes.pythonapi.PyCObject_AsVoidPtr.restype = ctypes.c_void_p
        ctypes.pythonapi.PyCObject_AsVoidPtr.argtypes = [ctypes.py_object]
        hwnd = ctypes.pythonapi.PyCObject_AsVoidPtr(pycobject_hwnd)

        self.thumbnail = ctypes.c_long()
        hr = dwmapi.DwmRegisterThumbnail(
            hwnd, desktop, ctypes.byref(self.thumbnail))

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(200)

    def refresh(self):
        thumbprop = ThumbProp()
        thumbprop.dwFlags = (
            DWM_TNP_RECTDESTINATION |
            DWM_TNP_VISIBLE |
            DWM_TNP_SOURCECLIENTAREAONLY
        )
        rc = self.rect()
        thumbprop.rcDestination.left = rc.left()
        thumbprop.rcDestination.top = rc.top()
        thumbprop.rcDestination.right = rc.right()
        thumbprop.rcDestination.bottom = rc.bottom()
        thumbprop.fSourceClientAreaOnly = 0
        thumbprop.fVisible = 1
        dwmapi.DwmUpdateThumbnailProperties(
            self.thumbnail, ctypes.byref(thumbprop))

dwmapi = ctypes.windll.dwmapi
app = QApplication([])
w = Widget()
w.showMaximized()
app.exec_()
