# coding: utf8
'''
Keys:
    Alt-U       Switch to 1st window without panel
    Alt-I       Switch to 2nd window without panel
    Alt-O       Switch to 3rd window without panel
    Alt-P       Switch to 4th window without panel
    Alt-J       Switch to 5th window without panel
    Alt-K       Switch to 6th window without panel
    Alt-L       Switch to 7th window without panel
    Alt-;       Switch to 8th window without panel

    Alt-1       Switch to  9th window without panel
    Alt-2       Switch to 10th window without panel
    Alt-3       Switch to 11th window without panel
    Alt-4       Switch to 12th window without panel
    Alt-5       Switch to 13th window without panel
    Alt-6       Switch to 14th window without panel
    Alt-7       Switch to 15th window without panel
    Alt-8       Switch to 16th window without panel
    Alt-9       Switch to 17th window without panel
    Alt-0       Switch to 18th window without panel

    Ctrl-Alt-<key>   Switch to the <key> window with panel
    Alt-Shift-<key>  Pin to <key> window

    Alt-,       Switch to prev without panel
    Alt-.       Switch to prev without panel

    Ctrl-Alt-D  Switch to prev with panel
    Ctrl-Alt-F  Switch to next with panel

Bugs:
    !!) thumb flash between frameless & framed

Todos:
    ) workspace
    ) similar window replace previous closed slot (chrome)
    ) memorized pin (window title? executable path?)
    ) custom regex slot rule (chrome, vim)
    .) detect window open/close (Lingoes Ctrl-Alt-E)
    .) GUI key config (conflicts resolution and other settings)
    ..) window thumbnail image data
'''
import logging
from datetime import datetime
from ctypes import windll
from collections import OrderedDict

import win32gui
import win32con
import pywintypes
from f6 import each
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from keyboard import Keyboard
from window import RendableWindows
import config

logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
#logger.setLevel(logging.WARNING)
#logging.getLogger('keyboard').setLevel(logging.INFO)
#logging.getLogger('window').setLevel(logging.DEBUG)

# https://msdn.microsoft.com/en-us/library/windows/desktop/dd375731(v=vs.85).aspx
SEMICOLON = chr(0xba)
PERIOD = chr(0xbe)
COMMA = chr(0xbc)
SLASH = chr(0xbf)
TAB = chr(win32con.VK_TAB)
CAPS = chr(win32con.VK_CAPITAL)

# 18 directly switch hotkeys
# e.g. Alt-U => 1st, Alt-I => 2nd, ..., Alt-1 => 9th, Alt-0 => 18th
DIRECT_SWITCH_HOTKEYS = 'UIOPJKL' + SEMICOLON + '1234567890'
DIRECT_SWITCH_HOTKEY_NAMES = 'UIOPJKL;1234567890'

class Res(object):

    def __init__(self):
        self.pin_icon = QPixmap('./img/pin.png').scaled(
            16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)

        self.setWindowFlags(Qt.SplashScreen
                            | Qt.FramelessWindowHint
                            | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background:transparent;")
        # hot key must be register after those setWindowFlags/setAttribute
        # guess Windows is identifying our window based on that

        self.res = Res()

        self.kbd = kbd = Keyboard()
        self._hotkey_handlers = {}
        self._hotkey_ids_when_active = []
        on_hotkey = self.on_hotkey

        # ctrl alt to for panel
        kbd.on('ctrl alt', self.on_activate)
        kbd.on('alt ctrl', self.on_activate)
        kbd.on('ctrl alt^', self.on_deactivate)
        kbd.on('alt ctrl^', self.on_deactivate)
        # right alt for seeing time with one hand
        kbd.on('ralt', self.on_activate)
        kbd.on('ralt^', self.on_deactivate)

        # switch/pin to prev/next
        on_hotkey('alt', COMMA, self.switch_to_prev)
        on_hotkey('alt shift', COMMA, self.pin_to_prev)
        on_hotkey('alt', PERIOD, self.switch_to_next)
        on_hotkey('alt shift', PERIOD, self.pin_to_next)
        # directly switch hotkeys
        for i, ch in enumerate(DIRECT_SWITCH_HOTKEYS):
            on_hotkey('alt', ch, self.switch_to_index, args=(i,))
            on_hotkey('alt shift', ch, self.pin_to_index, args=(i,))

        self.datetime_timer = QTimer()
        self.datetime_timer.timeout.connect(self.update)

        self.active = False
        self.wnds = RendableWindows(self)

    def switch_to_index(self, i):
        logger.debug('switch to {} [1..)'.format(i + 1))
        wnds = self.wnds
        wnds.update()
        if i < 0 or i >= len(wnds) or not wnds[i]:
            logger.info('switch failed, index {} has no window'.format(i))
            return False
        wnds[i].activate()
        return True

    def switch_to_index_and_hide(self, idx):
        logger.debug('switch_to_index_and_hide', idx)
        self.switch_to_index(idx)
        self.hide()

    def switch_to_prev(self):
        logger.info('switch prev')
        wnds = self.wnds
        wnds.update()
        if wnds.has_current:
            wnds.prev.activate()
        self.update()

    def switch_to_next(self):
        logger.info('switch next')
        wnds = self.wnds
        wnds.update()
        if wnds.has_current:
            wnds.next.activate()
        self.update()

    def pin_to_index(self, idx):
        wnds = self.wnds
        if not wnds.has_current:
            logger.warning('try to pin without current')
            return False
        logger.info('{} pin to {}'.format(wnds.current.index, idx))
        wnds.update()
        r = wnds.current.pin_to(idx)
        wnds.update()
        self.update()
        return r

    def pin_to_prev(self):
        logger.info('pin to prev')
        wnds = self.wnds
        self.pin_to_index(wnds.index(wnds.prev))

    def pin_to_next(self):
        logger.info('pin to next')
        wnds = self.wnds
        self.pin_to_index(wnds.index(wnds.next))

    def on_hotkey(self, modifiers, ch, callback, args=(), ephemeral=False):
        """Register <modifiers>-<key> with callback

        At least one of Ctrl/Alt/Shift must be present.

        Args:
            modifiers - a `str` to specify modifiers
                e.g. 'alt' / 'alt shift' / 'ctrl alt'
        """
        modifiers = modifiers.lower().split()
        alt = 'alt' in modifiers
        ctrl = 'ctrl' in modifiers
        shift = 'shift' in modifiers
        if not ctrl and not alt and not shift:
            raise TypeError('At least one of Ctrl/Alt/Shift must be present.')
        ctrl = win32con.MOD_CONTROL if ctrl else 0
        shift = win32con.MOD_SHIFT if shift else 0
        alt = win32con.MOD_ALT if alt else 0

        key = ord(ch)
        logger.info('registering {}-{} (0x{:02x})'.format(
            '-'.join(modifiers), ch, key))
        id = len(self._hotkey_handlers)
        if args is None:
            args = (ch,)
        self._hotkey_handlers[id] = (callback, args)
        hwnd = self.winId()
        modifiers = ctrl | alt | shift
        win32gui.RegisterHotKey(
            hwnd, id, modifiers, key)
        if ephemeral:
            self._hotkey_ids_when_active.append(id)
        return id

    def on_activate(self):
        self.activate()

    def activate(self):
        if self.active:
            return
        logger.info('activate')
        self.active = True
        self.wnds.update()
        self.datetime_timer.start(100)
        on_hotkey = self.on_hotkey
        # directly switch hotkeys
        for i, ch in enumerate(DIRECT_SWITCH_HOTKEYS):
            on_hotkey('ctrl alt', ch, self.switch_to_index, args=(i,),
                      ephemeral=True)
        # panel switch to prev/next
        on_hotkey('ctrl alt', 'F', self.switch_to_next, ephemeral=True)
        on_hotkey('ctrl alt', 'D', self.switch_to_prev, ephemeral=True)
        #on_hotkey('ctrl alt', COMMA, self.switch_to_prev, ephemeral=True)
        #on_hotkey('ctrl alt', PERIOD, self.switch_to_next, ephemeral=True)
        self.show_panel()

    def show_panel(self):
        rc_screen = QDesktopWidget().screenGeometry()
        ratio = min(config.SIZE_RATIO, 1.0)
        if ratio == 1.0:
            self.showMaximized()
        else:
            width = rc_screen.width() * ratio
            height = rc_screen.height() * ratio
            self.resize(width, height)
            self.show()

    def on_deactivate(self):
        self.deactivate()
        self.wnds.update()

    def deactivate(self):
        if not self.active:
            return
        logger.info('deactivate')
        self.active = False
        self.datetime_timer.stop()
        hwnd = self.winId()
        for id in self._hotkey_ids_when_active:
            windll.user32.UnregisterHotKey(int(hwnd), id)
        del self._hotkey_ids_when_active[:]
        self.hide()

    def winEvent(self, msg):
        if msg.message == win32con.WM_HOTKEY:
            id = msg.wParam
            callback, args = self._hotkey_handlers.get(id)
            if callback:
                callback(*args)
                return True, 0
            else:
                return False, 0
        return False, 0

    def paintEvent(self, ev):
        painter = QPainter(self)
        fm = painter.fontMetrics()
        wnds = self.wnds
        n_rows, n_cols = get_rowcols(wnds)
        # white pen
        color = QColor(config.TITLE_COLOR)
        pen = painter.pen()
        pen.setColor(color)
        painter.setPen(pen)
        # darken background
        color = QColor(config.BACK_COLOR)
        color.setAlpha(int(255 * (max(0.0, min(config.DARKEN_RATIO, 1.0)))))
        painter.fillRect(self.rect(), color)
        # metrics
        canvas_width = self.width()
        canvas_height = self.height()
        left_margin = canvas_width * config.LEFT_MARGIN_RATIO
        right_margin = canvas_width * config.RIGHT_MARGIN_RATIO
        top_margin = canvas_height * config.TOP_MARGIN_RATIO
        bottom_margin = canvas_height * config.BOTTOM_MARGIN_RATIO
        board_width = canvas_width - left_margin - right_margin
        board_height = canvas_height - top_margin - bottom_margin
        slot_width = board_width / float(n_cols)
        slot_height = board_height / float(n_rows)
        horz_gap = max(slot_width * config.HORZ_GAP_RATIO, 1)
        vert_gap = max(slot_width * config.VERT_GAP_RATIO, fm.lineSpacing())
        item_width = (board_width - (n_cols - 1) * horz_gap) / float(n_cols)
        item_height = (board_height - (n_rows - 1) * vert_gap) / float(n_rows)
        # probe layout
        layouts = do_layout(
            wnds, left_margin, top_margin, item_width, item_height,
            n_rows, n_cols, horz_gap, vert_gap)
        # actual metrics
        item_height = max(lt['rc_thumb'].height() for lt in layouts)
        vert_save = board_height - (item_height + vert_gap) * n_rows - vert_gap
        top_margin += vert_save / 2.0
        old_bottom_margin = bottom_margin
        bottom_margin += vert_save / 2.0
        # actual layout
        layouts = do_layout(
            wnds, left_margin, top_margin, item_width, item_height,
            n_rows, n_cols, horz_gap, vert_gap)
        # painting
        for i, lt in enumerate(layouts):
            wnd = lt['wnd']
            row = lt['row']
            rc_item = lt['rc_item']
            rc_thumb = lt['rc_thumb']
            if wnd:
                wnd.render(rc_thumb)
            # dummy also draw title inorder to have marker
            draw_title(painter, lt, res=self.res)
        rc_bottom = QRect(0, canvas_height - old_bottom_margin,
                          canvas_width, old_bottom_margin)
        draw_datetime(painter, rc_bottom)

def do_layout(wnds, xbeg, ybeg, item_width, item_height, n_rows, n_cols,
              horz_gap, vert_gap):
    layouts = []
    item_wh_ratio = item_width / float(item_height)
    for row in xrange(n_rows):
        for col in xrange(n_cols):
            i_wnd = row * n_cols + col
            if i_wnd == len(wnds):
                break
            wnd = wnds[i_wnd]
            x = xbeg + (item_width + horz_gap) * col
            y = ybeg + (item_height + vert_gap) * row
            rc_item = QRect(x, y, item_width, item_height)
            if wnd:
                wh_ratio = wnd.width / float(wnd.height)
                if wh_ratio > item_wh_ratio:
                    thumb_width = min(item_width, wnd.width)
                    thumb_height = thumb_width / wh_ratio
                else:
                    thumb_height = min(item_height, wnd.height)
                    thumb_width = thumb_height * wh_ratio
                x_offset = (item_width - thumb_width) / 2.0
                y_offset = (item_height - thumb_height) / 2.0
                rc_thumb = QRect(x + x_offset, y + y_offset,
                                 thumb_width, thumb_height)
            else:
                rc_thumb = QRect()
            layouts.append({
                'wnd': wnd,
                'row': row,
                'col': col,
                'rc_item': rc_item,
                'rc_thumb': rc_thumb,
            })
    rc_thumbs = [lt['rc_thumb'] for lt in layouts]
    max_thumb_height = max(rc.height() for rc in rc_thumbs)
    dummy_thumb_margin = (rc_item.height() - max_thumb_height) / 2.0
    for lt in layouts:
        wnd = lt['wnd']
        rc_item = lt['rc_item']
        if not wnd:
            lt['rc_thumb'] = rc_item.adjusted(0, dummy_thumb_margin,
                                              0, -dummy_thumb_margin)
    # row metrics
    for row in xrange(n_rows):
        i = row * n_cols
        lts = layouts[i:i+n_cols]
        rc_thumbs = list(each(lts)['rc_thumb'])
        each(lts)['min_thumb_top'] = min(rc.top() for rc in rc_thumbs)
        each(lts)['max_thumb_bottom'] = max(rc.bottom() for rc in rc_thumbs)
    return layouts

def draw_dummy_thumb(painter, layout, ch):
    rc_item = layout['rc_item']
    painter.save()
    font = painter.font()
    font.setPixelSize(min(rc_item.height() * 0.25, 30))
    painter.setFont(font)
    pen = painter.pen()
    color = QColor('#fff')
    color.setAlpha(25)
    pen.setColor(color)
    painter.setPen(pen)
    painter.drawText(rc_item, Qt.AlignCenter, '({}) Available'.format(ch))
    painter.restore()

def draw_title(painter, layout, res):
    wnd = layout['wnd']
    rc_item = layout['rc_item']
    max_thumb_bottom = layout['max_thumb_bottom']
    fm = painter.fontMetrics()
    i = wnd.index
    if i < 18:
        ch = DIRECT_SWITCH_HOTKEY_NAMES[i]
    else:
        ch = ''
    title_width = rc_item.width()
    marker = u'({})'.format(ch) if ch else ''
    marker_width = max(fm.boundingRect(marker).width(), 15)
    marker_gap = 10
    title_width -= marker_width + marker_gap
    marker_height = fm.lineSpacing()
    baseline = max_thumb_bottom + fm.lineSpacing()
    rc_item_marker = QRect(rc_item.left(), baseline + 3 - marker_height,
                      marker_width, marker_height)
    if wnd.pinned:
        pin_icon_width = res.pin_icon.width()
        pin_icon_gap = 5
        title_width -= pin_icon_width + pin_icon_gap
        x = rc_item.right() - res.pin_icon.width()
        y = baseline - fm.strikeOutPos() - res.pin_icon.height() / 2
        painter.drawPixmap(x, y, res.pin_icon)
    # draw marker
    if wnd:
        painter.drawText(rc_item_marker, Qt.AlignCenter, marker)
    else:
        draw_dummy_thumb(painter, layout, ch)
    # draw title
    title = fm.elidedText(wnd.title, Qt.ElideRight, title_width)
    x = rc_item_marker.right() + marker_gap
    if wnd.current:
        painter.save()
        pen = painter.pen()
        pen.setColor(QColor(config.ACTIVE_TITLE_COLOR))
        painter.setPen(pen)
        painter.drawText(x, baseline, title)
        painter.restore()
    else:
        painter.drawText(x, baseline, title)

def draw_datetime(painter, rc):
    painter.save()
    font = painter.font()
    font.setPixelSize(30)
    painter.setFont(font)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    painter.drawText(rc, Qt.AlignCenter, now)
    painter.restore()

def get_rowcols(wnds):
    n = len(wnds)
    if n <= 4:
        rows = 1
        cols = n
    elif n <= 8:
        rows = 2
        cols = 4
    elif n <= 12:
        rows = 3
        cols = 4
    elif n <= 16:
        rows = 4
        cols = 4
    else:
        rows = (n + 3) // 4
        cols = 4
    return rows, cols

app = QApplication([])

font = app.font()
font.setFamily('Consolas')
app.setFont(font)

w = Widget()
app.exec_()
