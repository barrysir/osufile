import collections
import itertools
from typing import TextIO
from dataclasses import dataclass, astuple, fields
from functools import reduce
from .datatypes import *
import warnings

# --- Util functions ---
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

# --- ParserPair ---
# namedtuple to store a parsing/writing function if you wanna use it
ParserPair = collections.namedtuple('ParserPair', ['parse', 'write'])

def ptuple(parsers, optionals=[]):
    parse_types,write_types = unzipl(parsers)
    def parse(data):
        if len(data) + len(optionals) < len(parse_types):
            raise TypeError("parser requires at least {} arguments but only {} were given".format(
                len(parse_types) - len(optionals),
                len(data)
            ))
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

# --- Parser ---
class Parser:
    # simple parsers
    parse_bool = lambda x: bool(int(x))
    write_bool = lambda x: str(int(x))
    parse_int = lambda x: int(round(float(x)))
    write_int = lambda x: str(int(x))
    parse_float = float
    write_float = str

    def __init__(self):
        # lookup tables are created in the constructor rather than set as static variables
        # to allow for inheritance (need a reference to 'self')

        # base types used by lookup tables
        cls = self.__class__
        self.osu_int = osu_int = ParserPair(cls.parse_int, cls.write_int)
        self.osu_float = osu_float = ParserPair(cls.parse_float, cls.write_float)
        self.osu_bool = osu_bool = ParserPair(cls.parse_bool, cls.write_bool)

        # create type lookup tables 
        self.METADATA_TYPES = self.init_metadata_lookup_table()
        self.init_timingpoint_lookup_tables()
        self.init_hitobject_lookup_tables()

    def parse(self, file: TextIO) -> OsuFile:
        """
        Parse a .osu file from a file object
        Returns an OsuFile
        """
        def sections(file):
            'Returns iterator of (section name, iterator of lines in section)'
            for section,lines in spliton(map(str.strip, file), lambda line: line.startswith('[')):
                if section is None: continue        # ignore everything before the first section
                section = section[1:-1]
                yield section,lines
    
        def scrub(lines):    
            for line in lines:
                # line = line.strip()       # has already been stripped in sections()
                if line == '': continue
                if line.startswith('//'): continue
                yield line

        osu = OsuFile()

        header = next(file).strip()
        osu.header = header

        for section,lines in sections(file):
            if section in {'General', 'Editor', 'Metadata', 'Difficulty'}:
                valid_metadata = filter(lambda kv: kv is not None, (self.parse_metadata(section, line) for line in lines))
                osu[section] = {key:val for key,val in valid_metadata}
            elif section in {'TimingPoints'}:
                tps = filter(lambda tp: tp is not None, map(self.parse_timingpoint, lines))
                osu[section] = list(tps)
            elif section in {'HitObjects'}:
                objs = filter(lambda i: i is not None, map(self.parse_hitobject, lines))
                osu[section] = list(objs)
            elif section in {'Events'}:
                lines = scrub(lines)
                osu[section] = [line.split(',') for line in lines]
            else:
                osu.setdefault(section, list(lines))
        
        return osu

    def write(self, file: TextIO, osu: OsuFile) -> None:            
        file.write(osu.header + '\n')
        for section in osu.keys():
            file.write('\n')    #formatting line
            file.write('[{}]\n'.format(section))

            if section in {'General', 'Editor', 'Metadata', 'Difficulty'}:
                for keyval in osu[section].items():
                    file.write('{}\n'.format(self.write_metadata(section, keyval)))
            elif section in {'TimingPoints'}:
                for tp in osu[section]:
                    file.write('{}\n'.format(self.write_timingpoint(tp)))
            elif section in {'HitObjects'}:
                for obj in osu[section]:
                    file.write('{}\n'.format(self.write_hitobject(obj)))
            elif section in {'Events'}:
                for obj in osu[section]:
                    file.write(','.join(obj) + '\n')
            else:
                for line in osu[section]:
                    file.write(line + '\n')
    
# ---------------------------------
#   Metadata sections
# ---------------------------------
    def parse_metadata(self, section: str, line: str) -> (str, any):
        key,hasSeparator,val = line.partition(':')
        if not hasSeparator:
            return None
        key = key.strip()
        val = self.lookup_metadata_parser(section, key).parse(val.strip())
        return (key,val)
    
    def write_metadata(self, section: str, keyval: (str, any)) -> str:
        key,val = keyval
        val = self.lookup_metadata_parser(section, key).write(val)
        return '{}:{}'.format(key, val)

    def lookup_metadata_parser(self, section: str, key: str) -> ParserPair:
        return self.METADATA_TYPES[section].get(key, ParserPair(str, str))

# ---------------------------------
#   Hit objects
# ---------------------------------
    HITTYPE_CIRCLE = 1 << 0
    HITTYPE_SLIDER = 1 << 1
    HITTYPE_SPINNER = 1 << 3
    HITTYPE_HOLD = 1 << 7
    HITTYPE_NEWCOMBO = 1 << 2

    HITSOUND_NORMAL = 1 << 0
    HITSOUND_WHISTLE = 1 << 1
    HITSOUND_FINISH = 1 << 2
    HITSOUND_CLAP = 1 << 3

    def init_hitobject_lookup_tables(self):
        osu_int = self.osu_int
        osu_float = self.osu_float
        osu_bool = self.osu_bool
        osu_str = ParserPair(str,str)
        hitsample = ParserPair(self.parse_hitsample, self.write_hitsample)
        def slider_curve():
            ptparse = plist_split('|', ptuple_split(":", [osu_int, osu_int]))
            def parse(obj):
                # split the first item P|308:266|266:254|...
                t,_,pts = obj.partition('|')
                pts = ptparse.parse(pts)
                return t,pts
            def write(obj):
                t,pts = obj
                pts = ptparse.write(pts)
                return t + '|' + pts
            return ParserPair(parse, write)

        self.HITOBJECT_HEADER = unzipl([osu_int, osu_int, osu_int, osu_int, osu_int])
        self.HITCIRCLE_TYPES = unzipl([hitsample])
        self.SPINNER_TYPES = unzipl([osu_int, hitsample])
        self.SLIDER_TYPES = ptuple([
            slider_curve(),
            osu_int,
            osu_float, 
            plist_split("|", ptry(osu_int, 0)),                      # edgeSounds
            plist_split("|", ptuple_split(":", [osu_int, osu_int])),    # edgeSets
            hitsample
        ], optionals=[None, [], [], self.default_hitsample()])
        self.HOLD_ENDTIME_TYPE = osu_int
        
        self.HITSAMPLE_TYPES = unzipl([osu_int, osu_int, osu_int, osu_int, osu_str])
        self.HEADER_SIZE = len(self.HITOBJECT_HEADER[0])

    def default_hitsample(self):
        return HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename='')
    
    def parse_hitobject(self, line):
        tokens = line.split(',')
        raw_header, raw_others = tokens[:self.HEADER_SIZE], tokens[self.HEADER_SIZE:]
        header = typed(self.HITOBJECT_HEADER[0], raw_header)
        hittype = header[3]
        if hittype & self.HITTYPE_CIRCLE:
            if len(raw_others) == 0:
                hitsample = self.default_hitsample()
            elif raw_others[0].strip() == '':
                hitsample = self.default_hitsample()
            else:
                (hitsample,) = typed(self.HITCIRCLE_TYPES[0], raw_others)
            return HitCircle(*header, hitsample)
        elif hittype & self.HITTYPE_HOLD:
            endtime,hitsample = self.parse_hold_sample(raw_others[0])
            return Hold(*header, endtime, hitsample)
        elif hittype & self.HITTYPE_SPINNER:
            others = typed(self.SPINNER_TYPES[0], raw_others)
            return Spinner(*header, *others)
        elif hittype & self.HITTYPE_SLIDER:
            others = self.parse_slider_params(raw_others)
            return Slider(*header, *others)
        else:
            return RawHitObject(*header, raw_others)

    def write_hitobject(self, obj):
        objdata = astuple_nonrecursive(obj)
        header, others = objdata[:self.HEADER_SIZE], objdata[self.HEADER_SIZE:]
        raw_header = typed(self.HITOBJECT_HEADER[1], header)
        if isinstance(obj, HitCircle):
            raw_others = typed(self.HITCIRCLE_TYPES[1], others)
        elif isinstance(obj, Hold):
            endtime,sample = others
            raw_others = [self.write_hold_sample(endtime, sample)]
        elif isinstance(obj, Spinner):
            raw_others = typed(self.SPINNER_TYPES[1], others)
        elif isinstance(obj, Slider):
            raw_others = self.write_slider_params(others)
        elif isinstance(obj, RawHitObject):
            raw_others = others
        # "header + others": can only concatenate list (not "tuple") to list
        # so we'll use this way of concatenating iterables
        return ','.join([*raw_header, *raw_others])

    def parse_hitsample(self, string):
        return HitSample(*typed(self.HITSAMPLE_TYPES[0], string.split(":")))

    def write_hitsample(self, sample):
        return ':'.join(typed(self.HITSAMPLE_TYPES[1], astuple_nonrecursive(sample)))
    
    def parse_hold_sample(self, string):
        endtime,_,sample = string.partition(':')
        return self.HOLD_ENDTIME_TYPE[0](endtime), self.parse_hitsample(sample)
    
    def write_hold_sample(self, endtime, sample):
        endtime = self.HOLD_ENDTIME_TYPE[1](endtime)
        sample = self.write_hitsample(sample)
        return endtime + ':' + sample
    
    def parse_slider_params(self, params):
        def fillexact(arr, size, obj):
            if len(arr) < size:
                arr.extend([obj] * (size-len(arr)))
            elif len(arr) > size:
                del arr[size:]
        
        (curvetype,curvepoints),repeats,length,edgesounds,edgesets,sample = self.SLIDER_TYPES.parse(params)
        
        if length is None:
            warnings.warn("Length is missing from slider data. Parser cannot calculate length, so it will set the length to 0.")
            length = 0
        fillexact(edgesounds, len(curvepoints), 0)
        fillexact(edgesets, len(curvepoints), (0,0))
        
        return (curvetype,curvepoints,repeats,length,edgesounds,edgesets,sample)

    def write_slider_params(self, slider):
        params = [slider[0:2], *slider[2:]]
        return self.SLIDER_TYPES.write(params)
    
# ---------------------------------
#   Timing points
# ---------------------------------
    def init_timingpoint_lookup_tables(self):
        osu_int = self.osu_int
        osu_float = self.osu_float
        osu_bool = self.osu_bool
        self.TIMINGPOINT_PARSE_TYPE,self.TIMINGPOINT_WRITE_TYPE = unzipl([osu_int, osu_float, osu_int, osu_int, osu_int, osu_int, osu_bool, osu_int])

    def parse_timingpoint(self, line):
        tokens = line.split(',')
        # structured so that a timing point with invalid argument types will be ignored,
        # but too few arguments will throw an exception
        def construct_tp(time, tick, meter, sampleset, sampleindex=0, volume=100, uninherited=True, effects=0):
            return TimingPoint(time, tick, meter, sampleset, sampleindex, volume, uninherited, effects)
            
        try:
            args = typed(self.TIMINGPOINT_PARSE_TYPE, tokens)
        except:
            return None
        return construct_tp(*args)

    def write_timingpoint(self, tp):
        return ','.join(typed(self.TIMINGPOINT_WRITE_TYPE, astuple_nonrecursive(tp)))

    # --- other stuff ---
    def init_metadata_lookup_table(self):
        osu_int = self.osu_int
        osu_float = self.osu_float
        osu_bool = self.osu_bool
        return {
            'General': {
                'AudioLeadIn': osu_int,
                'PreviewTime': osu_int,
                'Countdown': osu_int,
                'StackLeniency': osu_float,
                'Mode': osu_int,
                'LetterboxInBreaks': osu_bool,
                'StoryFireInFront': osu_bool,
                'EpilepsyWarning': osu_bool,
                'CountdownOffset': osu_int,
                'WidescreenStoryboard': osu_bool,
                'SpecialStyle': osu_bool,
                'UseSkinSprites': osu_bool,
                'SamplesMatchPlaybackRate': osu_bool,
                'AlwaysShowPlayfield': osu_bool
            },
            'Editor': {
                'Bookmarks': ParserPair(
                    lambda s: [osu_int.parse(i) for i in s.split(',')],
                    lambda t: ','.join(map(osu_int.write,t))
                ),
                'DistanceSpacing': osu_float,
                'BeatDivisor': osu_int,
                'GridSize': osu_int,
                'TimelineZoom': osu_float,
            },
            'Metadata': {
                'BeatmapID': osu_int,
                'BeatmapSetID': osu_int,
                'Tags': ParserPair(
                    lambda s: s.strip().split(' '),
                    lambda t: ' '.join(t)
                ),
            },
            'Difficulty': {
                'HPDrainRate': osu_float,
                'CircleSize': osu_float,
                'OverallDifficulty': osu_float,
                'ApproachRate': osu_float,
                'SliderMultiplier': osu_float,
                'SliderTickRate': osu_float,
            },
        }