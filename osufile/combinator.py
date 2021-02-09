# --- mini parser combinator library ---
 
import collections 
from functools import reduce

# --- ParserPair: namedtuple to store a parsing/writing function ---
ParserPair = collections.namedtuple('ParserPair', ['parse', 'write'])

# --- utils ---
def typed(types, items):
    'convert a tuple of items to certain types'
    return [t(s) for t,s in zip(types, items)]

def unzip(args):
    'unzip lists -> unzip([(1,4), (2,5), (3,6)]) = [(1,2,3), (4,5,6)]'
    return zip(*args)

def unzipl(args):
    'unzip, but returns a list instead of an iterator'
    return list(unzip(args))
    
def compose(*fns):
    'compose(f,g,h,...) -> returns a function f(g(h(...))'
    return reduce(lambda f, g: lambda *args: f(g(*args)), fns)

# --- combinators ---
def ptuple(parsers, optionals=[]):
    parse_types,write_types = unzipl(parsers)
    def parse(data):
        if len(data) + len(optionals) < len(parse_types):
            raise TypeError(f"parser requires at least {len(parse_types) - len(optionals)} arguments but only {len(data)} were given")
        parsed = list(typed(parse_types, data))
        if len(parsed) < len(parse_types):
            num_to_extend = len(parse_types) - len(parsed)
            assert num_to_extend > 0
            parsed.extend(optionals[-num_to_extend:])
        return tuple(parsed)

    def write(obj):
        return typed(write_types, obj)
    return ParserPair(parse, write)
 
def plist(parser):
    def parse(data):
        return list(map(parser.parse, data))
    def write(obj):
        return list(map(parser.write, obj))
    return ParserPair(parse, write)

def psplit(sep):
    def parse(data):
        return data.split(sep)
    def write(obj):
        return sep.join(obj)
    return ParserPair(parse, write)

def ptry(parser, return_on_fail):
    def parse(data):
        try:
            return parser.parse(data)
        except:
            return return_on_fail
    return ParserPair(parse, parser.write)

def pcompose(*parsers):
    # parsing: parsers[0](parsers[1](...(data)))
    # writing: writers[-1](writers[-2](...(obj)))
    p,w = unzipl(parsers)
    parse = compose(*p)
    write = compose(*w[::-1])
    return ParserPair(parse, write)

plist_split = lambda sep, parser: pcompose(plist(parser), psplit(sep))
ptuple_split = lambda sep, parsers: pcompose(ptuple(parsers), psplit(sep))