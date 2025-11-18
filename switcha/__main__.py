import sys
import signal
from datetime import datetime
from functools import partial

from fans.logger import get_logger
from fans.os.hotkey import global_hotkey_enabled
from fans.os.keyboard import Keyboard

from switcha.qt import *
from switcha import draw
from switcha.slots import Slots
from switcha.layout import layout_grids
from switcha.windows import Windows


logger = get_logger(__name__)


SWITCH_HOTKEYS = [
    'U', 'I', 'O', 'P',
    'J', 'K', 'L', ';',
    '7', '8', '9', '0',
]


@global_hotkey_enabled
class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # NOTE: hotkey require <modifier>+<key>, so use fans.os.keyboard instead
        self.kbd = Keyboard()
        self.kbd.on('alt shift',    self.show_panel)
        self.kbd.on('shift alt',    self.show_panel)
        self.kbd.on('alt^',         self.hide_panel)
        self.kbd.on('shift^',       self.hide_panel)
        self.kbd.on('alt shift^',   self.enter_arrange_mode)

        reg = self.register_global_hotkey
        for index, hotkey in enumerate(SWITCH_HOTKEYS):
            hotkey = _to_win_key(hotkey)
            reg(f'ctrl alt {hotkey}', partial(self.activate_window, index))

        self.arrange_mode = False
        self.windows = Windows(surface_hwnd=self.winId())
        self.slots = Slots(self.windows.update)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update)

    def show_panel(self):
        self.exit_arrange_mode()

        if not self.isVisible():
            # NOTE: use hotkey so key event won't propagate to foreground window
            reg = self.register_global_hotkey
            for index, hotkey in enumerate(SWITCH_HOTKEYS):
                hotkey = _to_win_key(hotkey)
                reg(f'alt shift {hotkey}', partial(self.activate_window, index))
                reg(f'alt {hotkey}', partial(self.arrange_window, index))

            self.slots.update()
            self.refresh_timer.start(100)
            self.showMaximized()

    def hide_panel(self):
        if self.isVisible():
            unreg = self.unregister_global_hotkey
            for hotkey in SWITCH_HOTKEYS:
                hotkey = _to_win_key(hotkey)
                unreg(f'alt shift {hotkey}')
                unreg(f'alt {hotkey}')
            self.hide()
            self.refresh_timer.stop()

    def enter_arrange_mode(self):
        self.arrange_mode = True

    def exit_arrange_mode(self):
        self.arrange_mode = False

    def activate_window(self, index):
        if window := self.slots.get_item(index):
            window.activate()

    def arrange_window(self, index):
        if self.isVisible() and self.arrange_mode:
            if (window := self.windows.current_window):
                self.slots.swap(self.slots.index(window), index)

    def refresh(self):
        self.slots.update()
        self.update()

    def paintEvent(self, ev):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        try:
            slots = self.slots
            current_window = self.windows.current_window
            fm = painter.fontMetrics()
            layout = layout_grids(
                slots.n_rows, slots.n_cols,
                self.width(), self.height(),
                title_height=2 * fm.lineSpacing(),
            )

            draw.draw_panel_background(QRect(*layout.panel_rect), painter=painter)

            for i, (slot, grid) in enumerate(zip(slots, layout.grids)):
                hotkey = SWITCH_HOTKEYS[i] if i < len(SWITCH_HOTKEYS) else None

                if (window := slot.item):
                    draw.draw_thumb(
                        window.thumb,
                        QRect(*grid.thumb_rect),
                        painter.device().devicePixelRatioF(),
                    )
                    draw.draw_icon(window.icon, QRect(*grid.icon_rect), painter=painter)
                    draw.draw_title(window.title, QRect(*grid.title_rect), painter=painter)
                    if hotkey:
                        draw.draw_hotkey(hotkey, QRect(*grid.hotkey_rect), painter=painter)
                    if window == current_window:
                        color = self.arrange_mode and '#2E9AFE' or '#fff'
                        draw.draw_border(QRect(*grid.grid_rect), color, painter=painter)
                else:
                    draw.draw_available_slot(hotkey, QRect(*grid.grid_rect), painter=painter)

            datetime_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            draw.draw_datetime(datetime_str, self.rect(), painter=painter)
        finally:
            painter.end()


def _to_win_key(hotkey):
    # https://msdn.microsoft.com/en-us/library/windows/desktop/dd375731(v=vs.85).aspx
    match hotkey:
        case ';':
            return chr(0xba)
        case _:
            return hotkey


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)

    font = app.font()
    font.setFamily('Microsoft YaHei')
    font.setWeight(QFont.Normal)
    app.setFont(font)

    main_window = MainWindow()

    sys.exit(app.exec())
