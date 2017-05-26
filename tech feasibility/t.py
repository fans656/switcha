import ctypes
from ctypes import c_uint, c_int, POINTER
import win32con
from PySide.QtCore import *
from PySide.QtGui import *

user32 = ctypes.windll.user32
SetWindowsHookEx = user32.SetWindowsHookExA

class KBDLLHOOKSTRUCT(ctypes.Structure):

    _fields_ = [
        ('vkCode', ctypes.c_uint),
        ('scanCode', ctypes.c_uint),
        ('flags', ctypes.c_uint),
        ('time', ctypes.c_uint),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)),
    ]

@ctypes.WINFUNCTYPE(c_uint, c_int, c_uint, c_uint)
def callback(nCode, wParam, lParam):
    hs = KBDLLHOOKSTRUCT.from_address(lParam)
    #print nCode, wParam, hs.vkCode, hs.scanCode
    if hs.vkCode == win32con.VK_LMENU:
        print 'intercept lmenu', 'down' if wParam in (
            win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN) else 'up'
        return 1
    elif hs.vkCode == ord('1'):
        print 'intercept 1', 'down' if wParam in (
            win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN) else 'up'
        return 1
    return 0

SetWindowsHookEx(win32con.WH_KEYBOARD_LL, callback, 0, 0)
app = QApplication([])
app.exec_()
