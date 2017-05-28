import logging

SIZE_RATIO = 1
DARKEN_RATIO = 0.90
BACK_COLOR = '#000'
TITLE_COLOR = '#aaa'
ACTIVE_TITLE_COLOR = '#4FE44A'

TOP_MARGIN_RATIO = BOTTOM_MARGIN_RATIO = 0.1
LEFT_MARGIN_RATIO = RIGHT_MARGIN_RATIO = 0.08
HORZ_GAP_RATIO = VERT_GAP_RATIO = 0.1

level = logging.DEBUG
level = logging.INFO

logging.basicConfig(
    format='%(asctime)15s %(name)8s %(levelname)8s %(message)s',
    #level=level,
)
