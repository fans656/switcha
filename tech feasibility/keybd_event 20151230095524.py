'''
https://msdn.microsoft.com/en-us/library/windows/desktop/ms646304(v=vs.85).aspx

seems like keybd_event is putting keyboard message into the system queue
so any focused window will receive it
'''
import time
import win32api
import win32con

def press(key, up=False):
    if isinstance(key, str):
        key = ord(key.upper())
    flags = win32con.KEYEVENTF_KEYUP if up else 0
    win32api.keybd_event(key, 0, flags, 0)

def tap(key):
    press(key)
    press(key, up=True)

time.sleep(0.5)
press(win32con.VK_LWIN)
tap('R')
press(win32con.VK_LWIN, up=True)
time.sleep(0.5)
for ch in 'notepad':
    tap(ch)
    time.sleep(0.1)
tap(win32con.VK_RETURN)
time.sleep(0.5)
for ch in 'hello world':
    tap(ch)
    time.sleep(0.1)
