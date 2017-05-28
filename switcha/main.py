# coding: utf8
'''
Bugs:
    ) run, win-e to open a new explorer, alt-0 to switch to last => Exception
    ) run, open many explorer, ctrl-alt invoke panel, new windows don't show up

Todos:
    ) Trim window title by pixel width, not char length
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
from window import Windows
import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
#logger.setLevel(logging.WARNING)
#logging.getLogger('keyboard').setLevel(logging.INFO)

HORZ_MARGIN_RATIO = 0.08
VERT_MARGIN_RATIO = 0.1
HORZ_GAP_RATIO = 0.1
VERT_GAP_RATIO = 0.1

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

        self.wnds = Windows(self)

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

        # white pen
        color = QColor(config.TITLE_COLOR)
        pen = painter.pen()
        pen.setColor(color)
        painter.setPen(pen)

        # darken background
        color = QColor(config.BACK_COLOR)
        color.setAlpha(int(255 * (max(0.0, min(config.DARKEN_RATIO, 1.0)))))
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
            n_rows = (n + 3) // 4
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
                wnd.render(rc)

                # draw title
                hotkey = HOTKEYS_WHEN_ACTIVE_REVERSE_INDEXES.get(
                    i_wnd, None)
                lim = 25
                title = wnd.title
                title = title[:lim] + ('...' if len(title) > lim else '')
                if hotkey is not None:
                    title = u'【{}】'.format(hotkey) + title
                if wnd.current:
                    painter.save()
                    pen = painter.pen()
                    pen.setColor(QColor(config.ACTIVE_TITLE_COLOR))
                    painter.setPen(pen)
                painter.drawText(rc.left(), rc.bottom() + 20, title)
                if wnd.current:
                    painter.restore()

                i_wnd += 1

        painter.save()
        font = painter.font()
        font.setPixelSize(30)
        painter.setFont(font)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        painter.drawText(self.rect(), Qt.AlignBottom | Qt.AlignCenter, now)
        painter.restore()

app = QApplication([])

font = app.font()
font.setFamily('Consolas')
app.setFont(font)

w = Widget()
app.exec_()
