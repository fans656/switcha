# convert hIcon to QPixmap
# https://evilcodecave.wordpress.com/2009/08/03/qt-undocumented-from-hicon-to-qpixmap/
import ctypes
import struct
from ctypes import wintypes, windll

import win32con
import win32gui
from fans.logger import get_logger

from switcha.qt import *


logger = get_logger(__name__)

user32 = windll.user32
gdi32 = windll.gdi32


def icon_from_path(path) -> 'QPixmap':
    try:
        large_icon_handles, small_icon_handles = win32gui.ExtractIconEx(path, 0)
    except pywintypes.error:
        return QPixmap()

    icon_handles = large_icon_handles + small_icon_handles

    if not icon_handles:
        return QPixmap()

    try:
        return hicon2pixmap(icon_handles[0])
    finally:
        for icon_handle in icon_handles:
            win32gui.DestroyIcon(icon_handle)


class ICONINFO(ctypes.Structure):

    _fields_ = [
        ('fIcon', wintypes.BOOL),
        ('xHotspot', wintypes.DWORD),
        ('yHotspot', wintypes.DWORD),
        ('hbmMask', wintypes.HBITMAP),
        ('hbmColor', wintypes.HBITMAP),
    ]

class RGBQUAD(ctypes.Structure):

    _fields_ = [
        ('rgbBlue', wintypes.BYTE),
        ('rgbGreen', wintypes.BYTE),
        ('rgbRed', wintypes.BYTE),
        ('rgbReserved', wintypes.BYTE),
    ]

class BITMAPINFOHEADER(ctypes.Structure):

    _fields_ = [
        ('biSize', wintypes.DWORD),
        ('biWidth', wintypes.LONG),
        ('biHeight', wintypes.LONG),
        ('biPlanes', wintypes.WORD),
        ('biBitCount', wintypes.WORD),
        ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD),
        ('biXPelsPerMeter', wintypes.LONG),
        ('biYPelsPerMeter', wintypes.LONG),
        ('biClrUsed', wintypes.DWORD),
        ('biClrImportant', wintypes.DWORD),
    ]

class BITMAPINFO(ctypes.Structure):

    _fields_ = [
        ('bmiHeader', BITMAPINFOHEADER),
        ('bmiColors', RGBQUAD),
    ]


def hicon2pixmap(icon_handle):
    screen = win32gui.GetDC(0)
    hdc = win32gui.CreateCompatibleDC(screen)
    win32gui.ReleaseDC(0, screen)

    # GetIconInfo returns a tuple: (fIcon, xHotspot, yHotspot, hbmMask, hbmColor)
    iconinfo = win32gui.GetIconInfo(icon_handle)
    if not iconinfo:
        logger.warning('convert hIcon to QPixmap failed')
        return QPixmap()

    # Unpack the tuple
    fIcon, xHotspot, yHotspot, hbmMask, hbmColor = iconinfo

    w = xHotspot * 2
    h = yHotspot * 2

    bitmapInfo = BITMAPINFOHEADER()
    bitmapInfo.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bitmapInfo.biWidth = w
    bitmapInfo.biHeight = h
    bitmapInfo.biPlanes = 1
    bitmapInfo.biBitCount = 32
    bitmapInfo.biCompression = win32con.BI_RGB
    bitmapInfo.biSizeImage = 0
    bitmapInfo.biXPelsPerMeter = 0
    bitmapInfo.biYPelsPerMeter = 0
    bitmapInfo.biClrUsed = 0
    bitmapInfo.biClrImportant = 0

    bits = ctypes.POINTER(wintypes.DWORD)()
    winBitmap = gdi32.CreateDIBSection(
        hdc,
        ctypes.byref(bitmapInfo),
        win32con.DIB_RGB_COLORS,
        ctypes.byref(bits),
        0, 0)
    oldhdc = win32gui.SelectObject(hdc, winBitmap)

    # Draw the icon
    win32gui.DrawIconEx(hdc, 0, 0, icon_handle, w, h, 0, 0, win32con.DI_NORMAL)

    image = from_hbitmap(hdc, winBitmap, w, h)
    foundAlpha = False
    for y in range(h):
        scanLine = image.scanLine(y)
        for x in range(w):
            i = x * 4
            rgb, = struct.unpack_from('=I', scanLine, i)
            if qAlpha(rgb):
                foundAlpha = True
        if foundAlpha:
            break
    if not foundAlpha:
        win32gui.DrawIconEx(hdc, 0, 0, icon_handle, w, h, 0, 0, win32con.DI_MASK)
        mask = from_hbitmap(hdc, winBitmap, w, h)
        for y in range(h):
            scanLineImage = image.scanLine(y)
            scanLineMask = 0 if mask.isNull() else mask.scanLine(y)
            for x in range(w):
                i = x * 4
                mask_val = struct.unpack('=I', scanLineMask[i:i+4])[0]
                if scanLineMask and qRed(mask_val):
                    scanLineImage[i:i+4] = struct.pack('=I', 0)
                else:
                    img_val = struct.unpack('=I', scanLineImage[i:i+4])[0]
                    img_val |= 0xff000000
                    scanLineImage[i:i+4] = struct.pack('=I', img_val)

    # Cleanup - use the handles from the tuple
    if hbmMask:
        win32gui.DeleteObject(hbmMask)
    if hbmColor:
        win32gui.DeleteObject(hbmColor)

    win32gui.SelectObject(hdc, oldhdc)
    win32gui.DeleteObject(winBitmap)
    win32gui.DeleteDC(hdc)
    return QPixmap.fromImage(image)


def from_hbitmap(hdc, hbitmap, w, h):
    bmi = BITMAPINFO()
    ctypes.memset(ctypes.byref(bmi), 0, ctypes.sizeof(bmi))
    bmi.bmiHeader.biSize        = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth       = w
    bmi.bmiHeader.biHeight      = -h
    bmi.bmiHeader.biPlanes      = 1
    bmi.bmiHeader.biBitCount    = 32
    bmi.bmiHeader.biCompression = win32con.BI_RGB
    bmi.bmiHeader.biSizeImage   = w * h * 4

    image = QImage(w, h, QImage.Format_ARGB32_Premultiplied)

    data = ctypes.create_string_buffer(bmi.bmiHeader.biSizeImage)
    memcpy = ctypes.cdll.msvcrt.memcpy
    if gdi32.GetDIBits(hdc, hbitmap, 0, h, data, ctypes.byref(bmi),
                       win32con.DIB_RGB_COLORS):
        for y in range(h):
            dest = image.scanLine(y)
            bpl = image.bytesPerLine()
            i = y * bpl
            dest[:] = data[i:i+bpl]
    else:
        logger.warning('converting hIcon to QPixmap, failed to get bitmap bits')
    return image
