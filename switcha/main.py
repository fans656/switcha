# coding: utf8
'''
Bugs:

Todos:
    ) window thumbnail image data
    ) Ctrl-Alt-[1-9] for non first 8 windows
'''
import logging
from datetime import datetime
from ctypes import windll
from collections import OrderedDict

import win32gui
import win32con
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from keyboard import Keyboard
from window import RendableWindows
import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
#logger.setLevel(logging.WARNING)
#logging.getLogger('keyboard').setLevel(logging.INFO)

VK_OEM_SEMICOLON = 0xba
VK_OEM_PERIOD = 0xbe
VK_OEM_2 = 0xbf
VK_OEM_COMMA = 0xbc

HOTKEYS_WHEN_ACTIVE = OrderedDict([
    ('U', 'U'),
    ('I', 'I'),
    ('O', 'O'),
    ('P', 'P'),
    ('J', 'J'),
    ('K', 'K'),
    ('L', 'L'),
    (chr(VK_OEM_SEMICOLON), ';'),
    ('M', 'M'),
    (chr(VK_OEM_COMMA), ','),
    (chr(VK_OEM_PERIOD), '.'),
    (chr(VK_OEM_2), '/'),
])
HOTKEYS_WHEN_ACTIVE_INDEXES = {
    ch: i for i, ch in enumerate(HOTKEYS_WHEN_ACTIVE.values()[:8])
}
HOTKEYS_WHEN_ACTIVE_REVERSE_INDEXES = {
    i: ch for ch, i in HOTKEYS_WHEN_ACTIVE_INDEXES.items()
}

class Widget(QDialog):

    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)

        self.setWindowFlags(Qt.SplashScreen
                            | Qt.FramelessWindowHint
                            | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background:transparent;")

        self.active = False

        self.keyboard = Keyboard()
        # ctrl alt to invoke panel
        self.keyboard.on('ctrl alt', self.on_activate)
        self.keyboard.on('alt ctrl', self.on_activate)
        #self.keyboard.on('lalt', self.on_activate)
        self.keyboard.on('ctrl alt^', self.on_deactivate)
        self.keyboard.on('alt ctrl^', self.on_deactivate)
        #self.keyboard.on('lalt^', self.on_deactivate)

        # hot key must be register after those setWindowFlags/setAttribute
        # guess Windows is identifying our window based on that
        self._hotkey_handlers = {}
        self._hotkey_ids_when_active = []

        # switch / pin
        for i, (ch, arg) in enumerate(HOTKEYS_WHEN_ACTIVE.items()):
            self.register_hotkey(ch, self.switch_to_index, args=(i,),
                                 alt=True)
            self.register_hotkey(ch, self.pin_to_index, args=(i,),
                                 alt=True, shift=True)

        # switch/pin to last (0)
        #self.register_hotkey('0', self.switch_to_last, args=(), alt=True)
        #self.register_hotkey('0', self.pin_to_last, args=(),
        #                     alt=True, shift=True)

        ## switch/pin to prev
        #self.register_hotkey('D', self.switch_to_prev, args=(), alt=True)
        #self.register_hotkey('D', self.pin_to_prev, args=(),
        #                     alt=True, shift=True)

        ## switch/pin to next
        #self.register_hotkey('F', self.switch_to_next, args=(), alt=True)
        #self.register_hotkey('F', self.pin_to_next, args=(),
        #                     alt=True, shift=True)

        self.wnds = RendableWindows(self)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)

    def switch_to_index(self, idx):
        logger.debug('switch to {} [1..)'.format(idx + 1))
        self.wnds.update()
        idx = min(idx, len(self.wnds) - 1)
        self.wnds[idx].activate()

    def switch_to_index_and_hide(self, idx):
        logger.debug('switch_to_index_and_hide', idx)
        self.switch_to_index(idx)
        self.hide()

    def switch_to_last(self):
        logger.debug('switch to last')
        self.wnds.update()
        self.wnds[-1].activate()

    def switch_to_prev(self):
        logger.debug('switch prev')
        self.wnds.update()
        self.wnds.prev.activate()

    def switch_to_next(self):
        logger.debug('switch next')
        self.wnds.update()
        self.wnds.next.activate()

    def pin_to_index(self, idx):
        self.wnds.update()
        wnds = self.wnds
        if not 0 <= idx < len(wnds):
            return False
        i, j = wnds.current_index, idx
        logger.info('pin to {} (original {})'.format(j, i))
        wnds[i], wnds[j] = wnds[j], wnds[i]
        self.wnds.update()
        return True

    def pin_to_last(self):
        logger.info('pin to last')
        self.pin_to_index(len(self.wnds) - 1)

    def pin_to_prev(self):
        logger.info('pin to prev')
        wnds = self.wnds
        self.pin_to_index(wnds.index(wnds.prev))

    def pin_to_next(self):
        logger.info('pin to next')
        wnds = self.wnds
        self.pin_to_index(wnds.index(wnds.next))

    def register_hotkey(self, ch, callback, args=None,
                        ctrl=False, alt=False, shift=False,
                        mod=0):
        """Register <modifiers>-<key> with callback

        At least one of Ctrl/Alt/Shift must be present,
        if all are unspecified, Ctrl-Alt-<key> will be used
        """
        if not ctrl and not alt and not shift:
            ctrl = alt = True
        ctrl = win32con.MOD_CONTROL if ctrl else 0
        shift = win32con.MOD_SHIFT if shift else 0
        alt = win32con.MOD_ALT if alt else 0

        key = ord(ch)
        logger.info('register {} (0x{:02x})'.format(ch, key))
        id = len(self._hotkey_handlers)
        if args is None:
            args = (ch,)
        self._hotkey_handlers[id] = (callback, args)
        hwnd = self.winId()
        modifiers = ctrl | alt | shift | mod
        win32gui.RegisterHotKey(
            hwnd, id, modifiers, key)
        return id

    def on_hotkey_when_active(self, ch):
        print 'on_hotkey_when_active', ch
        idx = HOTKEYS_WHEN_ACTIVE_INDEXES.get(ch, None)
        if idx is not None:
            self.switch_to_index_and_hide(idx)
            return
        if ch == ',':
            self.wnds.prev.activate()
            self.update()
            return
        if ch == '.':
            self.wnds.next.activate()
            self.update()
            return
        if ch.startswith('pin'):
            ch = ch[-1]
            idx = HOTKEYS_WHEN_ACTIVE_INDEXES.get(ch, None)
            if idx is not None:
                print 'pin to {} ({})'.format(ch, idx)
                self.pin_to_index(idx)
                self.update()
                return
            if ch == ',':
                self.wnds.prev.activate()
                self.update()
                return
            if ch == '.':
                self.wnds.next.activate()
                self.update()
                return

    def on_activate(self, _):
        self.activate()

    def activate(self):
        if self.active:
            return
        logger.info('activate')
        self.active = True
        self.wnds.update()
        self.timer.start(100)

        self._hotkey_ids_when_active = []
        for i, (ch, arg) in enumerate(HOTKEYS_WHEN_ACTIVE.items()):
            if not isinstance(ch, str):
                ch = chr(ch)
            id = self.register_hotkey(ch, self.on_hotkey_when_active,
                                      args=(arg,), ctrl=True, alt=True)
            self._hotkey_ids_when_active.append(id)
            id = self.register_hotkey(ch, self.on_hotkey_when_active,
                                      args=('pin ' + arg,),
                                      ctrl=True, alt=True, shift=True)
            self._hotkey_ids_when_active.append(id)
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

    def on_deactivate(self, _):
        self.deactivate()
        self.wnds.update()

    def deactivate(self):
        if not self.active:
            return
        logger.info('deactivate')
        self.active = False
        self.timer.stop()
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
        layouts, baselines = do_layout(
            wnds, left_margin, top_margin, item_width, item_height,
            n_rows, n_cols, horz_gap, vert_gap)
        # actual metrics
        rc_thumbs = [lt['rc_thumb'] for lt in layouts]
        item_width = max(rc.width() for rc in rc_thumbs)
        item_height = max(rc.height() for rc in rc_thumbs)
        horz_save = board_width - (item_width + horz_gap) * n_cols - horz_gap
        vert_save = board_height - (item_height + vert_gap) * n_rows - vert_gap
        left_margin += horz_save / 2.0
        top_margin += vert_save / 2.0
        right_margin += horz_save / 2.0
        old_bottom_margin = bottom_margin
        bottom_margin += vert_save / 2.0
        # actual layout
        layouts, baselines = do_layout(
            wnds, left_margin, top_margin, item_width, item_height,
            n_rows, n_cols, horz_gap, vert_gap)
        # painting
        for lt in layouts:
            wnd = lt['wnd']
            row = lt['row']
            rc_item = lt['rc_item']
            rc_thumb = lt['rc_thumb']
            if wnd:
                wnd.render(rc_thumb)
            if wnd:
                draw_title(painter, wnd, rc_item,
                           baselines[row] + fm.lineSpacing())
            else:
                draw_dummy_window(painter, rc_item)
        rc_bottom = QRect(0, canvas_height - old_bottom_margin,
                          canvas_width, old_bottom_margin)
        draw_datetime(painter, rc_bottom)

def do_layout(wnds, xbeg, ybeg, item_width, item_height, n_rows, n_cols,
              horz_gap, vert_gap):
    layouts = []
    baselines = {}
    item_wh_ratio = item_width / float(item_height)
    for row in xrange(n_rows):
        baseline = 0
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
            baseline = max(baseline, rc_thumb.bottom())
            layouts.append({
                'wnd': wnd,
                'row': row,
                'rc_item': rc_item,
                'rc_thumb': rc_thumb,
            })
        baselines[row] = baseline
    return layouts, baselines

def draw_dummy_window(painter, rc):
    painter.save()
    font = painter.font()
    font.setPixelSize(30)
    painter.setFont(font)
    pen = painter.pen()
    color = QColor('#fff')
    color.setAlpha(25)
    pen.setColor(color)
    painter.setPen(pen)
    painter.drawText(rc, Qt.AlignCenter, 'Available')
    painter.restore()

def draw_datetime(painter, rc):
    painter.save()
    font = painter.font()
    font.setPixelSize(30)
    painter.setFont(font)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    painter.drawText(rc, Qt.AlignCenter, now)
    painter.restore()

def draw_title(painter, wnd, rc_item, baseline):
    fm = painter.fontMetrics()
    marker_width = fm.boundingRect(u'【U】').width()
    title_width = rc_item.width() - marker_width
    title = fm.elidedText(wnd.title, Qt.ElideRight, title_width)
    x = rc_item.left() + marker_width
    if wnd.current:
        painter.save()
        pen = painter.pen()
        pen.setColor(QColor(config.ACTIVE_TITLE_COLOR))
        painter.setPen(pen)
        painter.drawText(x, baseline, title)
        painter.restore()
    else:
        painter.drawText(x, baseline, title)

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
