import ctypes
from ctypes import windll, wintypes
import functools

import win32gui
import win32api
import win32con
user32 = windll.user32

RIDEV_INPUTSINK = 0x100
WM_INPUT = 0xff
RID_INPUT = 0x10000003
MAPVK_VSC_TO_VK_EX = 3
RI_KEY_E0 = 2

msg2name = {v: k for k, v in win32con.__dict__.items() if k.startswith('WM_')}
vk2name = {v: k for k, v in win32con.__dict__.items() if k.startswith('VK_')}

VK_MENU = win32con.VK_MENU
VK_LMENU = win32con.VK_LMENU
VK_RMENU = win32con.VK_RMENU

VK_SHIFT = win32con.VK_SHIFT
VK_LSHIFT = win32con.VK_LSHIFT
VK_RSHIFT = win32con.VK_RSHIFT

VK_CONTROL = win32con.VK_CONTROL
VK_LCONTROL = win32con.VK_LCONTROL
VK_RCONTROL = win32con.VK_RCONTROL

class RAWINPUTDEVICE(ctypes.Structure):

    _fields_ = [
        ('usUsagePage', wintypes.USHORT),
        ('usUsage', wintypes.USHORT),
        ('dwFlags', wintypes.DWORD),
        ('hwndTarget', wintypes.HWND),
    ]

class RAWINPUTHEADER(ctypes.Structure):

    _fields_ = [
        ('dwType', wintypes.DWORD),
        ('dwSize', wintypes.DWORD),
        ('hDevice', wintypes.HANDLE),
        ('wParam', wintypes.WPARAM),
    ]

class RAWKEYBOARD(ctypes.Structure):

    _fields_ = [
        ('MakeCode', wintypes.USHORT),
        ('Flags', wintypes.USHORT),
        ('Reserved', wintypes.USHORT),
        ('VKey', wintypes.USHORT),
        ('Message', wintypes.UINT),
        ('ExtraInformation', wintypes.ULONG),
    ]

class RAWINPUT(ctypes.Structure):

    _fields_ = [
        ('header', RAWINPUTHEADER),
        ('keyboard', RAWKEYBOARD),
    ]

def differentiated_extendable_key(rk):
    # https://stackoverflow.com/a/18340130
    key = rk.VKey
    extended = rk.Flags & RI_KEY_E0
    if extended:
        if key == VK_CONTROL:
            key = VK_RCONTROL if extended else VK_LCONTROL
        if key == VK_MENU:
            key = VK_RMENU if extended else VK_LMENU
    else:
        key = win32api.MapVirtualKey(rk.MakeCode, MAPVK_VSC_TO_VK_EX) or key
    return key

class RawKeyEvent(object):

    def __init__(self, rk):
        key = differentiated_extendable_key(rk)
        self.Key = vk2name.get(key, chr(key))
        self.KeyID = key
        self.Message = rk.Message

def proc(onkey, hwnd, msg, wparam, lparam):
    if msg == WM_INPUT:
        hRawInput = lparam
        ri = RAWINPUT()
        cbSize = wintypes.UINT(ctypes.sizeof(ri))
        r = user32.GetRawInputData(
            hRawInput,
            RID_INPUT,
            ctypes.byref(ri),
            ctypes.byref(cbSize),
            ctypes.sizeof(RAWINPUTHEADER))
        rk = ri.keyboard
        ev = RawKeyEvent(ri.keyboard)
        onkey(ev)
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

def register_keyboard(onkey):
    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = functools.partial(proc, onkey)
    wc.lpszClassName = 'KeyListener'
    hinst = wc.hInstance = win32api.GetModuleHandle(None)
    classAtom = win32gui.RegisterClass(wc)
    hwnd = win32gui.CreateWindow(
        classAtom,
        'KeyListener',
        0,0,0,
        0, 0, # width, height
        0, 0,
        hinst, None
    )
    rid = RAWINPUTDEVICE()
    rid.usUsagePage = 1
    rid.usUsage = 6
    rid.dwFlags = RIDEV_INPUTSINK
    rid.hwndTarget = hwnd
    user32.RegisterRawInputDevices(
        ctypes.byref(rid), 1, ctypes.sizeof(RAWINPUTDEVICE)
    )

if __name__ == '__main__':
    def onkey(ev):
        print ev.Key, ev.KeyID

    register_keyboard(onkey)
    win32gui.PumpMessages()
