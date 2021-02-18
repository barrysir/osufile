import itertools
from dataclasses import fields
from functools import reduce

def spliton(it, pred, init=None):
    'Split an iterator on a predicate'
    curkey = init
    def key(x):
        nonlocal curkey
        if pred(x):
            curkey = x
        return curkey
    for i,j in itertools.groupby(it, key):
        next(j)
        yield (i,j)

def typed(types, items):
    'convert a tuple of items to certain types'
    return [t(s) for t,s in zip(types, items)]

def unzip(args):
    'unzip lists -> unzip([(1,4), (2,5), (3,6)]) = [(1,2,3), (4,5,6)]'
    return zip(*args)

def unzipl(args):
    'unzip, but returns a list instead of an iterator'
    return list(unzip(args))

def astuple_nonrecursive(dc):
    'dataclasses.astuple, but not recursive'
    return tuple(getattr(dc, field.name) for field in fields(dc))

def compose(*fns):
    'compose(f,g,h,...) -> returns a function f(g(h(...))'
    return reduce(lambda f, g: lambda *args: f(g(*args)), fns)