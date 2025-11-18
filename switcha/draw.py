import contextlib

from switcha.qt import *


def draw_panel_background(rect, *, painter):
    painter.fillRect(rect, QColor(0, 0, 0, int(0.8 * 255)))


def draw_thumb(thumb: 'Thumb', rect, pixel_ratio):
    thumb.render(rect, pixel_ratio)


def draw_icon(icon: 'QPixmap', rect, *, painter, padding_ratio=0.1, min_padding=5):
    with _painter_state(painter):
        padding = min(rect.height() * (1 - padding_ratio), min_padding)
        side = rect.height() - 2 * padding
        icon_rect = QRect(rect.left() + padding, rect.top() + padding, side, side)
        painter.drawPixmap(icon_rect, icon)


def draw_title(title: str, rect, *, painter):
    with _painter_state(painter, {
        'pen': lambda pen: pen.setColor(QColor('#fff')),
    }):
        title = painter.fontMetrics().elidedText(title, Qt.ElideRight, rect.width())
        painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, title)


def draw_hotkey(hotkey: str, rect, *, painter):
    with _painter_state(painter, {
        'pen': lambda pen: pen.setColor(QColor(255,255,255,100)),
        'font': lambda font: [
            font.setPixelSize(painter.fontMetrics().lineSpacing() * 1.2),
            font.setWeight(QFont.Black),
        ],
    }):
        painter.drawText(rect, Qt.AlignRight | Qt.AlignVCenter, hotkey)


def draw_available_slot(hotkey: str, rect, *, painter):
    with _painter_state(painter, {
        'pen': lambda pen: pen.setColor(QColor(255,255,255,50)),
        'font': lambda font: font.setPixelSize(min(rect.height() * 0.25, 30)),
    }):
        prefix = f'({hotkey})' if hotkey else ''
        painter.drawText(rect, Qt.AlignCenter, f'{prefix} Available')


def draw_border(rect, color, *, painter, width=2):
    with _painter_state(painter, {
        'pen': lambda pen: [
            pen.setColor(QColor(color)),
            pen.setWidth(width),
        ],
    }):
        painter.drawRect(rect.adjusted(-width, -width, width, width))


def draw_datetime(text, canvas_rect, *, painter, size=30):
    with _painter_state(painter, {
        'font': lambda font: [
            font.setPixelSize(size),
            font.setWeight(QFont.Black),
        ],
    }):
        font = painter.font()
        fm = QFontMetrics(font)
        bbox = fm.boundingRect(text)
        width, height = bbox.width(), bbox.height()
        width -= width % size + (size if width % size else 0)

        x = canvas_rect.width() - width / 2.0
        x = min(canvas_rect.width() - width - 2 * fm.lineSpacing(), x)

        text_rect = QRect(x, canvas_rect.bottom() - height, width, height)
        text_rect.translate(0, -fm.lineSpacing())

        painter.fillRect(text_rect.adjusted(-10,0,60,10), QColor(0,0,0))

        path = QPainterPath()
        path.addText(text_rect.left(), text_rect.bottom(), font, text)
        painter.fillPath(path, QColor('#ECF8FC'))
        painter.drawPath(path)


@contextlib.contextmanager
def _painter_state(painter, setup=lambda: None):
    painter.save()

    if callable(setup):
        setup()
    elif isinstance(setup, dict):
        if 'pen' in setup:
            pen = painter.pen()
            setup['pen'](pen)
            painter.setPen(pen)
        if 'font' in setup:
            font = painter.font()
            setup['font'](font)
            painter.setFont(font)
    else:
        raise ValueError('invalid setup')

    yield painter

    painter.restore()
