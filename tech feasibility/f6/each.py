'''
Succinct way to write `for` loop

>>> each('hello').upper()
['H', 'E', 'L', 'L', 'O']

is equaivalent to

>>> [c.upper() for c in 'hello']
['H', 'E', 'L', 'L', 'O']

>>> class Foo:
...     def __init__(self, x):
...         self.bar = Bar(x)

>>> class Bar:
...     def __init__(self, x):
...         self.x = x
...     def say(self):
...         print self.x
...         self.x += 1
...         return self.x

>>> a = [Foo(i) for i in range(3)]
>>> each(a).bar.say()
0
1
2
[1, 2, 3]

>>> each(a).foo = 3
>>> list(each(a).foo)
[3, 3, 3]
'''
import functools

class each(object):

    @staticmethod
    def v(f):
        '''
        vectorize f to operate on the first argument

        >>> def say(name, judgement):
        ...     print name, judgement

        >>> say('I', 'am sexy')
        I am sexy
        >>> each.v(say)(['Mary', 'Lita', 'Victoria'], 'is sexy')
        Mary is sexy
        Lita is sexy
        Victoria is sexy
        [None, None, None]
        '''
        @functools.wraps(f)
        def f_(xs, *args, **kwargs):
            rs = []
            for x in xs:
                r = f(x, *args, **kwargs)
                rs.append(r)
            return rs
        return f_

    def __init__(self, *args):
        if len(args) == 0:
            raise TypeError('each() expects at least 1 argument')
        elif len(args) == 1:
            arg = args[0]
            if hasattr(arg, '__call__'):
                f = arg
                return vectorized(f)
            else:
                iterable = arg
        else:
            iterable = args
        self.__iterable = iterable

    def __getattribute__(self, key):
        if key == '_each__iterable':
            return object.__getattribute__(self, key)
        else:
            return each(list(getattr(t, key) for t in self.__iterable))

    # >>> each(a).foo = 656
    def __setattr__(self, k, v):
        if k == '_each__iterable':
            super(each, self).__setattr__(k, v)
        else:
            for t in self.__iterable:
                setattr(t, k, v)
            return self

    # >>> each(a).f(ARGS)
    # >>> each(funcs)(ARGS)
    def __call__(self, *args, **kwargs):
        return [f(*args, **kwargs) for f in self.__iterable]

    # >>> list(each(a).foo)
    def __iter__(self):
        return iter(self.__iterable)

    def __repr__(self):
        return '<each of {}>'.format(self.__iterable)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
