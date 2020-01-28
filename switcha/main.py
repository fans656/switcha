# coding: utf8
'''
Usage:
    Ctrl-Alt-{keys} for quick switch without panel
    Shift-Alt-{keys} for visual switch with panel

    when panel is visible with Shift-Alt, relase shift will enter pin mode,
    and you can use {keys} to pin current window to a specific slot

    where {keys} is UIOPKL;123456789 and J(for Alt-Tab)

Bugs:
    ) alt-j sometimes nonfunctional
    ) datetime duplicate drawings
    ) on windows 10, sometimes background will lose transparency,
       thus become totally black
    ) when there is only 1 window, thumbnail appears too large

Todos:
    ) show 8 slots initialiy
    ) put window to KL slots initially
    ) restore state (based on hwnd/title/path)
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
import sys
import traceback
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from ctypes import windll
from collections import OrderedDict, Counter

import win32gui
import win32con
import pywintypes
from f6 import each
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from keyboard import Keyboard
from window import RendableWindows
import config
import utils

logger = logging.getLogger(__name__)
logger.addHandler(RotatingFileHandler('log.log', maxBytes=1024 * 1024, backupCount=1))
#logger.setLevel(logging.DEBUG)
#logger.setLevel(logging.INFO)
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
DIRECT_SWITCH_HOTKEYS = 'UIOPMKL' + SEMICOLON + '7890'
DIRECT_SWITCH_HOTKEY_NAMES = 'UIOPMKL;7890'

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

        kbd.on(config.panel_mod, self.activate)
        kbd.on(config.panel_mod_reversed, self.activate)
        kbd.on('alt^', self.deactivate)
        kbd.on('shift^', self.deactivate)

        kbd.on('alt shift^', self.enter_pin_mode)

        #on_hotkey(config.panel_mod, SLASH, self.toggle_hidden_windows)
        #on_hotkey(config.pin_mod, SLASH, self.hide_window)

        # right alt for seeing time with one hand
        kbd.on('ralt', self.on_activate)
        #kbd.on('ralt^', self.on_deactivate)

        on_hotkey(config.quick_mod, 'J', self.alt_tab)
        #on_hotkey(config.quick_mod_reversed, 'J', self.alt_tab)

        # switch/pin to prev/next
        on_hotkey(config.quick_mod, COMMA, self.switch_to_prev)
        #on_hotkey(config.quick_mod_reversed, COMMA, self.switch_to_prev)
        #on_hotkey(config.pin_mod, COMMA, self.pin_to_prev)

        on_hotkey(config.quick_mod, PERIOD, self.switch_to_next)
        #on_hotkey(config.quick_mod_reversed, PERIOD, self.switch_to_next)
        #on_hotkey(config.pin_mod, PERIOD, self.pin_to_next)
        # directly switch hotkeys
        for i, ch in enumerate(DIRECT_SWITCH_HOTKEYS):
            on_hotkey(config.quick_mod, ch, self.switch_to_index, args=(i,))
            if ch.isdigit():
                continue
            on_hotkey(config.pin_mod, ch, self.pin_to_index, args=(i,))

        self.datetime_timer = QTimer()
        self.datetime_timer.timeout.connect(self.update)

        self.active = False
        self.pin_mode = False
        self.hiding_hidden_windows = True
        self.wnds = RendableWindows(self)

    def enter_pin_mode(self):
        self.pin_mode = True

    def exit_pin_mode(self):
        self.pin_mode = False

    def toggle_hidden_windows(self):
        logger.info('toggle_hidden_windows')
        self.wnds.toggle_hidden()
        self.update()

    def hide_window(self):
        logger.info('hide_window TODO')
        return
        self.wnds.update()
        wnd = self.wnds.current
        if not wnd:
            logger.info('no active window to hide')
            return
        logger.info(u'hide window: {}'.format(wnd.title))
        wnd.hidden = not wnd.hidden
        self.wnds.update()
        self.update()

    def switch_to_index(self, i):
        logger.debug('switch_to_index {}'.format(i))
        wnds = self.wnds
        wnds.update()
        if i < 0 or i >= len(wnds) or not wnds[i]:
            logger.info('switch_to_index failed, no window at {}'.format(i))
            return False
        wnds[i].activate()
        return True

    def switch_to_index_and_hide(self, idx):
        logger.debug('switch_to_index_and_hide', idx)
        self.switch_to_index(idx)
        self.hide()

    def alt_tab(self):
        self.wnds.update()
        last_active = self.wnds.last_active
        if last_active:
            last_active.activate()
        else:
            target = self.wnds.last_active
            if target:
                target.activate()
        #target = self.wnds.alt_tab_target
        #if target:
        #    target.activate()
        #    logger.info('alt tab to "{}"'.format(target.title))
        #    print ('alt tab to "{}"'.format(target.title))
        #else:
        #    logger.warning('no alt-tab target')
        #    for i, wnd in enumerate(self.wnds):
        #        logger.warning('{:2} {}'.format(i, wnd.title))
        #        print ('{:2} {}'.format(i, wnd.title))

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
        if not self.pin_mode:
            return
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
        alt = 'alt' in modifiers or 'ralt' in modifiers
        ctrl = 'ctrl' in modifiers or 'rctrl' in modifiers
        shift = 'shift' in modifiers or 'rshift' in modifiers
        if not ctrl and not alt and not shift:
            raise TypeError('At least one of Ctrl/Alt/Shift must be present.')
        ctrl = win32con.MOD_CONTROL if ctrl else 0
        shift = win32con.MOD_SHIFT if shift else 0
        alt = win32con.MOD_ALT if alt else 0

        key = ord(ch)
        hotkey = '-'.join(modifiers)
        logger.debug('registering {}-{} (0x{:02x}) for {}'.format(
            hotkey, ch, key, callback.__name__))
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
            logger.warning('registering {}-{} (0x{:02x}) for {} failed'.format(
                hotkey, ch, key, callback.__name__))
            raw_input()
            #logger.warning(u'register hotkey {} failed, {}'.format(
            #    hotkey, e.strerror.decode(config.console_encoding)))
            return None
        if ephemeral:
            self._hotkey_ids_when_active.append(id)

    def on_activate(self):
        self.activate()

    def activate(self):
        self.exit_pin_mode()
        if self.active:
            #logger.debug('panel already activated')
            return
        logger.info('activating panel')
        self.wnds.update()
        self.datetime_timer.start(100)
        on_hotkey = self.on_hotkey
        # directly switch hotkeys
        for i, ch in enumerate(DIRECT_SWITCH_HOTKEYS):
            on_hotkey(config.panel_mod, ch, self.switch_to_index,
                      args=(i,), ephemeral=True)
        # panel switch to prev/next
        on_hotkey(config.panel_mod, 'F', self.switch_to_next, ephemeral=True)
        on_hotkey(config.panel_mod, 'D', self.switch_to_prev, ephemeral=True)
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
        self.active = True

    @utils.debug_call
    def on_deactivate(self):
        self.deactivate()
        self.wnds.update()

    @utils.debug_call
    def deactivate(self):
        if not self.active:
            #logger.debug('panel already deactivated')
            return
        logger.info('deactivating panel')
        self.pin_mode = False
        self.datetime_timer.stop()
        hwnd = self.winId()
        for id in self._hotkey_ids_when_active:
            windll.user32.UnregisterHotKey(int(hwnd), id)
        del self._hotkey_ids_when_active[:]
        self.hide()
        self.active = False

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
        # use majority's height as item_height
        counter = Counter(lt['rc_thumb'].height() for lt in layouts)
        item_height = sorted(counter.items(),
                             key=lambda (h, n): n, reverse=True)[0][0]
        #item_height = max(lt['rc_thumb'].height() for lt in layouts)
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
        for wnd in wnds.wnds:
            logger.info(wnd.path)
        # draw windows
        for i, lt in enumerate(layouts):
            wnd = lt['wnd']
            row = lt['row']
            rc_item = lt['rc_item']
            rc_item.adjust(0, 0, 0, fm.lineSpacing() * 2)  # for title area
            rc_thumb = lt['rc_thumb']
            wnd.ch = (DIRECT_SWITCH_HOTKEY_NAMES[wnd.index]
                      if wnd.index < 18 else '')
            if wnd:
                wnd.render(rc_thumb)
                draw_title(painter, lt, res=self.res)
                if wnd.active or wnd.previously_active:
                    draw_border(painter, rc_item, rc_thumb, wnd, self.pin_mode)
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
                if not wnd.width * wnd.height:
                    logger.warning(
                        u'zero sized window: title="{}", path="{}"'.format(
                            wnd.title, wnd.path))
                    continue
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
    old_fm = fm
    font = painter.font()
    font.setPixelSize(old_fm.lineSpacing() * 1.2)
    font.setWeight(QFont.Black)
    painter.setFont(font)
    fm = painter.fontMetrics()
    pen = painter.pen()
    color = QColor(config.MARKER_COLOR)
    color.setAlpha(100)
    pen.setColor(color)
    painter.setPen(pen)
    marker_width = fm.boundingRect('X').width()
    marker = ch
    if marker:
        painter.drawText(rc, Qt.AlignRight | Qt.AlignVCenter, marker)
        rc.adjust(0, 0, -(marker_width + fm.lineSpacing() * 0.4), 0)
    fm = old_fm
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

def draw_border(painter, rc_item, rc_thumb, wnd, pin_mode):
    fm = painter.fontMetrics()
    painter.save()
    if pin_mode:
        color = QColor('#2E9AFE')
    else:
        color = QColor(config.BORDER_COLOR)
    pen = painter.pen()
    if wnd.active:
        pen.setWidth(3)
        d = 5
        rc_border = rc_item.adjusted(-d, -d, d, -d)
    else:
        pen.setWidth(1)
        pen.setStyle(Qt.DashLine)
        color.setAlpha(200)
        d = 1
        rc_border = rc_thumb.adjusted(-d, -d, d, d)
    pen.setColor(color)
    painter.setPen(pen)
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

if __name__ == '__main__':
    try:
        app = QApplication([])

        font = app.font()
        font.setFamily('Microsoft YaHei')
        font.setWeight(QFont.Normal)
        app.setFont(font)

        w = Widget()
        app.exec_()
    except Exception as e:
        with open('dump.txt', 'w') as f:
            s = traceback.format_exc()
            QMessageBox.warning(None, 'switcha', s)
            f.write(s)
