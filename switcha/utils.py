import functools
import logging
import time

logger = logging.getLogger(__name__)

def debug_call(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        logger.debug('{{ {}'.format(f.__name__))
        res = f(*args, **kwargs)
        logger.debug('}}  {}'.format(f.__name__))
        return res
    return wrapper

def timeit(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        beg = time.time()
        res = f(*args, **kwargs)
        logger.debug('{}() execute {}ms'.format(
            f.__name__, (time.time() - beg) * 1000))
        return res
    return wrapper
