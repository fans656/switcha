# coding: utf8
from ctypes import windll
import logging

import win32gui
import win32con
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from keyboard import Keyboard
from window import Windows
import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
#logger.setLevel(logging.WARNING)
logging.getLogger('keyboard').setLevel(logging.INFO)

HORZ_MARGIN_RATIO = 0.08
VERT_MARGIN_RATIO = 0.1
HORZ_GAP_RATIO = 0.1
VERT_GAP_RATIO = 0.1

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
        self._hotkey_handlers = {}

        # switch/pin to 1-9
        for i in xrange(1, 10):
            key = str(i)
            self.register_hotkey(key, self.switch_to_index, alt=True)
            self.register_hotkey(key, self.on_pin_to_index,
                                 alt=True, shift=True)

        # switch/pin to last (0)
        self.register_hotkey('0', self.switch_to_last, alt=True)
        self.register_hotkey('0', self.pin_to_last, alt=True, shift=True)

        # switch/pin to prev (k)
        self.register_hotkey('K', self.switch_to_prev, alt=True)
        self.register_hotkey('K', self.pin_to_prev, alt=True, shift=True)

        # switch/pin to next (j)
        self.register_hotkey('J', self.switch_to_next, alt=True)
        self.register_hotkey('J', self.pin_to_next, alt=True, shift=True)

        self.wnds = Windows(self)

    def switch_to_index(self, key):
        logger.debug('switch to {}'.format(chr(key)))
        self.wnds.update()
        idx = min(int(chr(key)) - 1, len(self.wnds) - 1)
        self.wnds[idx].activate()

    def switch_to_last(self, _):
        logger.debug('switch to last')
        self.wnds.update()
        self.wnds[-1].activate()

    def switch_to_prev(self, _):
        logger.debug('switch prev')
        self.wnds.update()
        self.wnds.prev.activate()

    def switch_to_next(self, _):
        logger.debug('switch next')
        self.wnds.update()
        self.wnds.next.activate()

    def on_pin_to_index(self, key):
        idx = int(chr(key)) - 1
        self.pin_to_index(idx)

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

    def pin_to_last(self, _):
        logger.info('pin to last')
        self.pin_to_index(len(self.wnds) - 1)

    def pin_to_prev(self, _):
        logger.info('pin to prev')
        wnds = self.wnds
        self.pin_to_index(wnds.index(wnds.prev))

    def pin_to_next(self, _):
        logger.info('pin to next')
        wnds = self.wnds
        self.pin_to_index(wnds.index(wnds.next))

    def register_hotkey(self, ch, callback,
                        ctrl=False, alt=False, shift=False):
        """Register <modifiers>-<key> with callback

        At least one of Ctrl/Alt/Shift must be present,
        if all are unspecified, Ctrl-Alt-<key> will be used
        """
        if not ctrl and not alt and not shift:
            ctrl = alt = True
        ctrl = win32con.MOD_CONTROL if ctrl else 0
        shift = win32con.MOD_SHIFT if shift else 0
        alt = win32con.MOD_ALT if alt else 0

        key = ord(ch.upper())
        logger.info('register Ctrl-Alt-{} (0x{:02x})'.format(ch, key))
        id = (len(self._hotkey_handlers) << 8) | key
        self._hotkey_handlers[id] = callback
        hwnd = self.winId()
        modifiers = ctrl | alt | shift
        win32gui.RegisterHotKey(
            hwnd, id, modifiers, key)

    def activate(self, show=True):
        logger.info('activate')
        print_wnds(self.wnds)
        show = False
        if show:
            rc_screen = QDesktopWidget().screenGeometry()
            ratio = min(config.SIZE_RATIO, 1.0)
            if ratio == 1.0:
                self.showMaximized()
            else:
                width = rc_screen.width() * ratio
                height = rc_screen.height() * ratio
                self.resize(width, height); self.show()

    def deactivate(self):
        logger.info('deactivate')
        self.hide()

    def winEvent(self, msg):
        if msg.message == win32con.WM_HOTKEY:
            id = msg.wParam
            callback = self._hotkey_handlers.get(id)
            if callback:
                callback(id & 0xff)
                return True, 0
            else:
                return False, 0
        return False, 0

    def paintEvent(self, ev):
        painter = QPainter(self)
        color = QColor('#000')
        color.setAlpha(180)
        painter.fillRect(self.rect(), color)

        wnds = self.wnds
        canvas_width = self.width()
        canvas_height = self.height()
        horz_margin = canvas_width * HORZ_MARGIN_RATIO
        vert_margin = canvas_height * VERT_MARGIN_RATIO
        board_width = canvas_width - 2 * horz_margin
        board_height = canvas_height - 2 * vert_margin

        n = len(wnds)
        if n <= 4:
            n_rows = 1
            n_cols = n
        elif n <= 8:
            n_rows = 2
            n_cols = 4
        elif n <= 12:
            n_rows = 3
            n_cols = 4
        elif n <= 16:
            n_rows = 4
            n_cols = 4
        else:
            n_rows = n // 4
            n_cols = 4

        slot_width = board_width / float(n_cols)
        slot_height = board_height / float(n_rows)
        horz_gap = slot_width * HORZ_GAP_RATIO
        vert_gap = slot_width * VERT_GAP_RATIO
        item_width = slot_width - 0.5 * horz_gap
        item_height = slot_height - 0.5 * vert_gap
        item_wh_ratio = item_width / item_height
        i_wnd = 0
        for row in xrange(n_rows):
            for col in xrange(n_cols):
                if i_wnd == len(wnds):
                    break
                wnd = wnds[i_wnd]
                x = horz_margin + (item_width + horz_gap) * col
                y = vert_margin + (item_height + vert_gap) * row

                wh_ratio = wnd.width / float(wnd.height)
                if wh_ratio > item_wh_ratio:
                    thumb_width = min(item_width, wnd.width)
                    thumb_height = thumb_width / wh_ratio
                else:
                    thumb_height = min(item_height, wnd.height)
                    thumb_width = thumb_height * wh_ratio
                x_offset = (item_width - thumb_width) / 2.0
                y_offset = (item_height - thumb_height) / 2.0
                x += x_offset
                y += y_offset
                rc = QRect(x, y, thumb_width, thumb_height)
                if wnd.current:
                    d = 10
                    rc_back = rc.adjusted(-d, -d, d, d)
                    painter.save()
                    color = QColor('#fff')
                    #color.setAlpha(200)
                    pen = painter.pen()
                    #pen.setWidth(1)
                    pen.setColor(color)
                    painter.setPen(pen)
                    painter.drawRect(rc_back)
                    painter.restore()
                wnd.render(rc)
                i_wnd += 1

app = QApplication([])
w = Widget()
app.exec_()
