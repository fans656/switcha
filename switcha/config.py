import logging

SIZE_RATIO = 0.5

level = logging.DEBUG
level = logging.INFO

logging.basicConfig(
    format='%(asctime)15s %(name)8s %(levelname)8s %(message)s',
    #level=level,
)
