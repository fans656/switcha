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

    Alt-Shift-<key>   Switch to the <key> window with panel
    Ctrl-Alt-<key>  Pin to <key> window

    Alt-,       Switch to prev without panel
    Alt-.       Switch to prev without panel

    Alt-Shift-D  Switch to prev with panel
    Alt-Shift-F  Switch to next with panel

Bugs:
    ) on windows 10, sometimes background will lose transparency,
       thus become totally black
    ) when there is only 1 window, thumbnail appears too large

Todos:
    ) when there are few windows (less than 5) map ctrl-alt-[1-5] to
      these windows, ease use for one hand
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

QMOD = config.quick_modifier
PMOD = config.pin_modifier
NMOD = config.panel_modifier

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

        # shift alt to for panel
        kbd.on(' '.join((QMOD, NMOD)), self.on_activate)
        kbd.on(' '.join((NMOD, QMOD)), self.on_activate)
        kbd.on(' '.join((QMOD, NMOD)) + '^', self.on_deactivate)
        kbd.on(' '.join((NMOD, QMOD)) + '^', self.on_deactivate)
        # right alt for seeing time with one hand
        kbd.on('ralt', self.on_activate)
        kbd.on('ralt^', self.on_deactivate)

        # alt-m for alt-tab
        on_hotkey(QMOD, 'M', self.alt_tab)

        # switch/pin to prev/next
        on_hotkey(QMOD, COMMA, self.switch_to_prev)
        on_hotkey(' '.join((QMOD, PMOD)), COMMA, self.pin_to_prev)
        on_hotkey(QMOD, PERIOD, self.switch_to_next)
        on_hotkey(' '.join((QMOD, PMOD)), PERIOD, self.pin_to_next)
        # directly switch hotkeys
        for i, ch in enumerate(DIRECT_SWITCH_HOTKEYS):
            on_hotkey(QMOD, ch, self.switch_to_index, args=(i,))
            on_hotkey(' '.join((QMOD, PMOD)), ch, self.pin_to_index, args=(i,))

        self.datetime_timer = QTimer()
        self.datetime_timer.timeout.connect(self.update)

        self.active = False
        self.wnds = RendableWindows(self)

    def switch_to_index(self, i):
        logger.info('switch to {} (1 based)'.format(i + 1))
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

    def alt_tab(self):
        self.wnds.last_active.activate()

    def switch_to_prev(self):
        logger.info('switch prev')
        wnds = self.wnds
        wnds.update()
        if wnds.has_current:
            wnds.prev.activate()
        elif wnds:
            wnds.last_active.activate()
        self.update()

    def switch_to_next(self):
        logger.info('switch next')
        wnds = self.wnds
        wnds.update()
        if wnds.has_current:
            wnds.next.activate()
        elif wnds:
            wnds.last_active.activate()
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
        hotkey = '-'.join(modifiers)
        logger.info('registering {}-{} (0x{:02x})'.format(
            hotkey, ch, key))
        id = len(self._hotkey_handlers)
        if args is None:
            args = (ch,)
        self._hotkey_handlers[id] = (callback, args)
        hwnd = self.winId()
        modifiers = ctrl | alt | shift
        try:
            win32gui.RegisterHotKey(
                hwnd, id, modifiers, key)
        except pywintypes.error as e:
            logger.warning(u'register hotkey {} failed, {}'.format(
                hotkey, e.strerror))
            return None
        if ephemeral:
            self._hotkey_ids_when_active.append(id)

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
            on_hotkey(' '.join((QMOD, NMOD)), ch, self.switch_to_index,
                      args=(i,), ephemeral=True)
        # panel switch to prev/next
        on_hotkey(' '.join((QMOD, NMOD)), 'F', self.switch_to_next, ephemeral=True)
        on_hotkey(' '.join((QMOD, NMOD)), 'D', self.switch_to_prev, ephemeral=True)
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
        wnds = self.wnds
        n_rows, n_cols = get_rowcols(wnds)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        fm = painter.fontMetrics()
        # white pen
        color = QColor(config.TITLE_COLOR)
        pen = painter.pen()
        pen.setColor(color)
        painter.setPen(pen)
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
        vert_gap = max(slot_width * config.VERT_GAP_RATIO,
                       fm.lineSpacing() * config.VERT_GAP_N_LINESPACING)
        item_width = (board_width - (n_cols - 1) * horz_gap) / float(n_cols)
        item_height = (board_height - (n_rows - 1) * vert_gap) / float(n_rows)
        # probing layout
        layouts, rc_bounding = do_layout(
            wnds, left_margin, top_margin, item_width, item_height,
            n_rows, n_cols, horz_gap, vert_gap)
        # actual metrics
        item_height = max(lt['rc_thumb'].height() for lt in layouts)
        vert_save = board_height - (item_height + vert_gap) * n_rows - vert_gap
        top_margin += vert_save / 2.0
        old_bottom_margin = bottom_margin
        bottom_margin += vert_save / 2.0
        # actual layout
        layouts, rc_bounding = do_layout(
            wnds, left_margin, top_margin, item_width, item_height,
            n_rows, n_cols, horz_gap, vert_gap)
        # draw darken back
        d = fm.lineSpacing() * 2
        rc_back = rc_bounding.adjusted(-d, -d, d, 1.5 * d)
        color = QColor(config.BACK_COLOR)
        color.setAlpha(int(255 * (max(0.0, min(config.DARKEN_RATIO, 1.0)))))
        painter.fillRect(rc_back, color)
        # draw windows
        for i, lt in enumerate(layouts):
            wnd = lt['wnd']
            row = lt['row']
            rc_item = lt['rc_item']
            rc_item.adjust(0, 0, 0, fm.lineSpacing() * 2)  # for title area
            rc_thumb = lt['rc_thumb']
            wnd.ch = (DIRECT_SWITCH_HOTKEY_NAMES[wnd.index]
                      if wnd.index < 18 else '')
            if wnd and wnd.current:
                draw_active_border(painter, rc_item)
            if wnd:
                wnd.render(rc_thumb)
                draw_title(painter, lt, res=self.res)
            else:
                draw_dummy_thumb(painter, lt)
        draw_datetime(painter, self.rect())

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
    left = top = float('inf')
    right = bottom = 0
    for lt in layouts:
        wnd = lt['wnd']
        rc_item = lt['rc_item']
        if not wnd:
            lt['rc_thumb'] = rc_item.adjusted(0, dummy_thumb_margin,
                                              0, -dummy_thumb_margin)
        left = min(left, rc_item.left())
        top = min(top, rc_item.top())
        right = max(right, rc_item.right())
        bottom = max(bottom, rc_item.bottom())
    # row metrics
    for row in xrange(n_rows):
        i = row * n_cols
        lts = layouts[i:i+n_cols]
        rc_thumbs = list(each(lts)['rc_thumb'])
        each(lts)['min_thumb_top'] = min(rc.top() for rc in rc_thumbs)
        each(lts)['max_thumb_bottom'] = max(rc.bottom() for rc in rc_thumbs)
    rc_bounding = QRect(left, top, right - left, bottom - top)
    return layouts, rc_bounding

def draw_dummy_thumb(painter, layout):
    rc_item = layout['rc_item']
    ch = layout['wnd'].ch
    painter.save()
    font = painter.font()
    font.setPixelSize(min(rc_item.height() * 0.25, 30))
    painter.setFont(font)
    pen = painter.pen()
    color = QColor('#fff')
    color.setAlpha(50)
    pen.setColor(color)
    painter.setPen(pen)
    painter.drawText(rc_item, Qt.AlignCenter, '({}) Available'.format(ch))
    painter.restore()

def draw_title(painter, layout, res):
    wnd = layout['wnd']
    rc_item = layout['rc_item']
    max_thumb_bottom = layout['max_thumb_bottom']
    ch = wnd.ch
    rc = QRect(rc_item)
    rc.setTop(max_thumb_bottom)
    fm = painter.fontMetrics()

    # draw marker (hotkey)
    painter.save()
    font = painter.font()
    font.setWeight(QFont.Black)
    painter.setFont(font)
    pen = painter.pen()
    pen.setColor(QColor('#555'))
    painter.setPen(pen)
    marker_width = fm.boundingRect('X').width()
    marker = ch
    if marker:
        painter.drawText(rc, Qt.AlignRight | Qt.AlignVCenter, marker)
        rc.adjust(0, 0, -(marker_width + 5), 0)
    painter.restore()

    # draw program icon
    painter.save()
    d = 2 * fm.lineSpacing()
    t = 5
    rc_icon = QRect(rc.left(), rc.top(), d, d).adjusted(t,t,-t,-t)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    painter.drawPixmap(rc_icon, wnd.icon)
    rc.setLeft(rc_icon.right() + d * 0.2)
    painter.restore()

    # draw pin icon
    if wnd.pinned:
        icon = res.pin_icon
        w, h = icon.width(), icon.height()
        x = rc.right() - w
        y = (rc.top() + rc.bottom()) / 2.0 - h / 2.0
        rc_pin = QRect(x, y, w, h)
        painter.drawPixmap(rc_pin, res.pin_icon)
        rc.adjust(0, 0, -w, 0)

    # draw title
    title = fm.elidedText(wnd.title, Qt.ElideRight, rc.width())
    painter.drawText(rc, Qt.AlignLeft | Qt.AlignVCenter, title)

def draw_active_border(painter, rc_item):
    fm = painter.fontMetrics()
    painter.save()
    pen = painter.pen()
    pen.setWidth(3)
    painter.setPen(pen)
    d = fm.lineSpacing() * 0.4
    rc_border = rc_item.adjusted(-d, -d, d, d)
    painter.drawRect(rc_border)
    painter.restore()

def draw_datetime(painter, rc_canvas):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    painter.save()

    font = painter.font()
    size = config.DATETIME_FONT_PIXEL_SIZE
    font.setPixelSize(size)
    font.setWeight(QFont.Black)

    fm = QFontMetrics(font)
    bbox = fm.boundingRect(now)
    width, height = bbox.width(), bbox.height()
    width -= width % size + (size if width % size else 0)
    x = rc_canvas.width() * config.DATETIME_HORZ_POS_RATIO - width / 2.0
    x = min(rc_canvas.width() - width - 2 * fm.lineSpacing(), x)
    rc_text = QRect(x, rc_canvas.bottom() - height, width, height)
    d = fm.lineSpacing() * config.DATETIME_VERT_MARGIN_LINESPACING_RATIO
    rc_text.translate(0, -d)

    path = QPainterPath()
    path.addText(rc_text.left(), rc_text.bottom(), font, now)

    pen = painter.pen()
    pen.setColor(QColor(config.DATETIME_OUTLINE_COLOR))
    painter.setPen(pen)

    painter.fillPath(path, QColor(config.DATETIME_COLOR))
    painter.drawPath(path)

    painter.restore()

def get_rowcols(wnds):
    n = len(wnds)
    cols = 4
    if n <= 4:
        rows = 1
    elif n <= 8:
        rows = 2
    elif n <= 12:
        rows = 3
    elif n <= 16:
        rows = 4
    else:
        rows = (n + 3) // 4
    return rows, cols

app = QApplication([])

font = app.font()
font.setFamily('Microsoft YaHei')
font.setWeight(QFont.Normal)
app.setFont(font)

w = Widget()
app.exec_()
