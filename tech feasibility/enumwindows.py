'''
http://www.thescarms.com/VBasic/alttab.aspx
'''
import win32process
import win32gui
import win32con

i = 1

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
    global i
    print i, hwnd, title
    i += 1
    if 'putty' in title.lower():
        win32gui.SetForegroundWindow(hwnd)

win32gui.EnumWindows(f, None)
