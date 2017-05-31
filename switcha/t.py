# coding: utf8
import win32gui
import win32process

from window import Windows


import win32api, win32con, win32process

def get_exepath(pid):
    handle = win32api.OpenProcess(
        win32con.PROCESS_ALL_ACCESS, False, pid)
    exe = win32process.GetModuleFileNameEx(handle, 0)
    return exe

wnds = Windows()
for wnd in wnds:
    tid, pid = win32process.GetWindowThreadProcessId(wnd.hwnd)
    path = get_exepath(pid)
    print win32gui.ExtractIconEx(path, 0)
