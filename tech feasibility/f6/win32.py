import win32process
import win32gui
import win32con

def task_windows():

    def f(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        if win32gui.GetParent(hwnd):
            return
        if win32gui.GetWindow(hwnd, win32con.GW_OWNER):
            return
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return
        windows.append((hwnd, title))

    windows = []
    win32gui.EnumWindows(f, None)
    return windows[:-1]
