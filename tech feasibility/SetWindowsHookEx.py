'''
http://stackoverflow.com/questions/9817531/applying-low-level-keyboard-hooks-with-python-and-setwindowshookexa/16430918#16430918
'''
import ctypes
from ctypes import c_uint, c_int
import win32con
from PySide.QtCore import *
from PySide.QtGui import *

user32 = ctypes.windll.user32
SetWindowsHookEx = user32.SetWindowsHookExA

@ctypes.WINFUNCTYPE(c_uint, c_int, c_uint, c_uint)
def callback(nCode, wParam, lParam):
    print nCode, wParam, lParam
    return 0

SetWindowsHookEx(win32con.WH_KEYBOARD_LL, callback, 0, 0)
app = QApplication([])
app.exec_()
