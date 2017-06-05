import logging

should_hides = [
    lambda w: w.path.lower().endswith('virtualbox.exe'),
]

quick_mod_key = 'alt'
pin_mod_key = 'ctrl'
panel_mod_key = 'shift'

quick_mod = quick_mod_key
panel_mod = ' '.join((quick_mod_key, panel_mod_key))
panel_modr = ' '.join((panel_mod_key, quick_mod_key))
pin_mod = ' '.join((quick_mod_key, pin_mod_key))

TOP_MARGIN_RATIO = BOTTOM_MARGIN_RATIO = 0.1
LEFT_MARGIN_RATIO = RIGHT_MARGIN_RATIO = 3 * (
    768 * BOTTOM_MARGIN_RATIO / 1366.0)
HORZ_GAP_RATIO = 0.05
VERT_GAP_RATIO = 0.02
VERT_GAP_N_LINESPACING = 2.0

SIZE_RATIO = 1
DARKEN_RATIO = 0.80
BACK_COLOR = '#000'
TITLE_COLOR = '#eee'
#ACTIVE_TITLE_COLOR = '#4FE44A'
BORDER_COLOR = '#fff'
SWITCHED_TITLE_COLOR = ''
PINNED_TITLE_COLOR = '#'
MARKER_COLOR = '#fff'

DATETIME_COLOR = '#ECF8FC'
DATETIME_OUTLINE_COLOR = '#222'
DATETIME_FONT_PIXEL_SIZE = 30
DATETIME_HORZ_POS_RATIO = 1.0
DATETIME_VERT_MARGIN_LINESPACING_RATIO = 1.0

console_encoding = 'gbk'

level = logging.DEBUG
level = logging.INFO

logging.basicConfig(
    #filename='log.log',
    format='%(asctime)15s %(name)8s %(levelname)8s %(message)s',
    #level=level,
)
