import logging

SIZE_RATIO = 1
DARKEN_RATIO = 0.90
BACK_COLOR = '#000'
TITLE_COLOR = '#aaa'
ACTIVE_TITLE_COLOR = '#4FE44A'

level = logging.DEBUG
level = logging.INFO

logging.basicConfig(
    format='%(asctime)15s %(name)8s %(levelname)8s %(message)s',
    #level=level,
)
