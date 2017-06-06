import functools
import logging

logger = logging.getLogger(__name__)

def debug_call(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        logger.debug('{{ {}'.format(f.__name__))
        res = f(*args, **kwargs)
        logger.debug('}}  {}'.format(f.__name__))
        return res
    return wrapper
