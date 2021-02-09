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

# --- mini parser combinator library ---
# namedtuple to store a parsing/writing function
ParserPair = collections.namedtuple('ParserPair', ['parse', 'write'])

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

# --- Parser ---
class Parser:
    # simple parsers
    def parse_bool(self, x): return bool(int(x))
    def write_bool(self, x): return str(int(x))
    def parse_int(self, x): return int(round(float(x)))
    def write_int(self, x): return str(int(x))
    def parse_float(self, x): return float(x)
    def write_float(self, x): return str(x)

    def __init__(self):
        # lookup tables are created in the constructor rather than as static variables
        # to allow for inheritance (if "parse_int" is changed in a subclass, the base class should use the subclass's implementation)
        # (need a reference to 'self')
        # could use metaclasses to generate the lookup table but it makes things complicated

        # base pairs which the lookup tables use
        self.osu_int = ParserPair(self.parse_int, self.write_int)
        self.osu_float = ParserPair(self.parse_float, self.write_float)
        self.osu_bool = ParserPair(self.parse_bool, self.write_bool)

        self.init_metadata_lookup_tables()
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
                osu[section] = self.parse_metadata_section(section, lines)
            elif section in {'TimingPoints'}:
                osu[section] = self.parse_timingpoint_section(section, lines)
            elif section in {'HitObjects'}:
                osu[section] = self.parse_hitobject_section(section, lines)
            elif section in {'Events'}:
                lines = scrub(lines)
                osu[section] = [line.split(',') for line in lines]
            else:
                osu.setdefault(section, list(lines))
        
        return osu

    def write(self, file: TextIO, osu: OsuFile) -> None:
        file.write('osu file format v14' + '\n')    # output is written in v14 format
        for section in osu.keys():
            file.write('\n')     #newline to make the formatting look good
            file.write(f'[{section}]\n')

            if section in {'General', 'Editor', 'Metadata', 'Difficulty'}:
                self.write_metadata_section(file, section, osu[section])
            elif section in {'TimingPoints'}:
                self.write_timingpoint_section(file, section, osu[section])
            elif section in {'HitObjects'}:
                self.write_hitobject_section(file, section, osu[section])
            elif section in {'Events'}:
                for obj in osu[section]:
                    file.write(','.join(obj) + '\n')
            else:
                for line in osu[section]:
                    file.write(line + '\n')

# ---------------------------------
#   Metadata sections
# ---------------------------------
    def parse_metadata_section(self, section, lines):
        def metadata():
            for line in lines:
                try:
                    yield self.parse_metadata(section, line)
                except Exception as ex: 
                    raise ValueError(f"failed to parse metadata {line!r}") from ex
        valid_metadata = filter(lambda kv: kv is not None, metadata())
        return {key:val for key,val in valid_metadata}
    
    def write_metadata_section(self, file, section, section_data):
        for keyval in section_data.items():
            file.write(f'{self.write_metadata(section, keyval)}\n')
    
    def parse_metadata(self, section: str, line: str) -> (str, any):
        key,sep,val = line.partition(':')
        if not sep:
            return None
        key = key.strip()
        val = self.lookup_metadata_parser(section, key).parse(val.strip())
        return (key,val)
    
    def write_metadata(self, section: str, keyval: (str, any)) -> str:
        key,val = keyval
        val = self.lookup_metadata_parser(section, key).write(val)
        return f'{key}:{val}'

    def lookup_metadata_parser(self, section: str, key: str) -> ParserPair:
        return self.METADATA_TYPES[section].get(key, ParserPair(str, str))

# ---------------------------------
#   Hit objects
# ---------------------------------
    HITTYPE_CIRCLE    = 0b00000001
    HITTYPE_SLIDER    = 0b00000010
    HITTYPE_NEWCOMBO  = 0b00000100
    HITTYPE_SPINNER   = 0b00001000
    HITTYPE_COMBOSKIP = 0b01110000
    HITTYPE_HOLD      = 0b10000000

    HITSOUND_NORMAL  = 0b00000001
    HITSOUND_WHISTLE = 0b00000010
    HITSOUND_FINISH  = 0b00000100
    HITSOUND_CLAP    = 0b00001000

    def init_hitobject_lookup_tables(self):
        # basic types
        osu_int = self.osu_int
        osu_float = self.osu_float
        osu_bool = self.osu_bool
        osu_str = ParserPair(str,str)

        # hit object types
        self.HITSAMPLE_TYPES = ptuple_split(':', [osu_int, osu_int, osu_int, osu_int, osu_str])
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

        # hit object header
        self.HITOBJECT_HEADER_TYPES = [osu_int, osu_int, osu_int, osu_int, osu_int]
        self.HITOBJECT_HEADER_SIZE = len(self.HITOBJECT_HEADER_TYPES)
        self.HITOBJECT_HEADER = ptuple(self.HITOBJECT_HEADER_TYPES)

        # hit object params
        self.HITCIRCLE_TYPES = ptuple([hitsample])
        self.SPINNER_TYPES = ptuple([osu_int, hitsample])
        self.SLIDER_TYPES = ptuple([
            slider_curve(),
            osu_int,
            osu_float, 
            plist_split("|", ptry(osu_int, 0)),                      # edgeSounds
            plist_split("|", ptuple_split(":", [osu_int, osu_int])),    # edgeSets
            hitsample
        ], optionals=[None, [], [], self.default_hitsample()])
        self.HOLD_ENDTIME_TYPE = osu_int

    def default_hitsample(self):
        return HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename='')
    
    def hitobject_whattype(self, objtype):
        '''
        Figure out what hitobject this is from the type bitmask (in case multiple bits are set)
        returns one of [self.HITTYPE_CIRCLE, self.HITTYPE_SLIDER, self.HITTYPE_SPINNER, self.HITTYPE_HOLD, None],
        None if the object does not match any of these types
        '''
        ordering = [self.HITTYPE_CIRCLE, self.HITTYPE_SLIDER, self.HITTYPE_SPINNER, self.HITTYPE_HOLD]
        for o in ordering:
            if objtype & o: return o
        return None
    
    def parse_hitobject_section(self, section, lines):
        def objs():
            for line in lines:
                try:
                    yield self.parse_hitobject(line)
                except Exception as ex:
                    raise ValueError(f"failed to parse hit object {line!r}") from ex
        return list(filter(lambda x: x is not None, objs()))

    def write_hitobject_section(self, file, section, section_data):
        for obj in section_data:
            file.write(self.write_hitobject(obj) + '\n')

    def parse_hitobject(self, line):
        # split header/others
        tokens = line.split(',')
        raw_header, raw_others = tokens[:self.HITOBJECT_HEADER_SIZE], tokens[self.HITOBJECT_HEADER_SIZE:]

        # parse header, and parse params using type from header
        header = self.HITOBJECT_HEADER.parse(raw_header)
        whatobj = self.hitobject_whattype(header[3])
        constructor, parser = {
            self.HITTYPE_CIRCLE:  (HitCircle, self.parse_hitcircle_params),
            self.HITTYPE_SLIDER:  (Slider, self.parse_slider_params),
            self.HITTYPE_SPINNER: (Spinner, self.parse_spinner_params),
            self.HITTYPE_HOLD:    (Hold, self.parse_hold_params),
            None:                 (RawHitObject, lambda raw_others: [raw_others])   # RawHitObject params = one argument, containing all parameters
        }[whatobj]
        others = parser(raw_others)
        return constructor(*header, *others)

    def write_hitobject(self, obj):
        # split data object into header/params
        objdata = astuple_nonrecursive(obj)
        header, others = objdata[:self.HITOBJECT_HEADER_SIZE], objdata[self.HITOBJECT_HEADER_SIZE:]

        # serialize params
        lookup_table = [
            (HitCircle, self.write_hitcircle_params),
            (Spinner, self.write_spinner_params),
            (Slider, self.write_slider_params),
            (Hold, self.write_hold_params),
            (RawHitObject, lambda id: id)
        ]
        for (type, writer) in lookup_table:
            if isinstance(obj, type):
                raw_others = writer(others)
                break
        else:
            assert False, f"unsupported obj of type {obj.__class__.__name__} passed to write_hitobject {obj!r}"

        # serialize header
        raw_header = self.HITOBJECT_HEADER.write(header)
        # header and others might be different types (list vs. tuple)
        # so we'll use this way of concatenating iterables
        return ','.join([*raw_header, *raw_others])

    def parse_hitsample(self, string):
        return HitSample(*self.HITSAMPLE_TYPES.parse(string))

    def write_hitsample(self, sample):
        return self.HITSAMPLE_TYPES.write(astuple_nonrecursive(sample))
    
    def parse_hitcircle_params(self, raw_params):
        if len(raw_params) == 0:
            hitsample = self.default_hitsample()
        elif raw_params[0].strip() == '':
            hitsample = self.default_hitsample()
        else:
            (hitsample,) = self.HITCIRCLE_TYPES.parse(raw_params)
        
        return [hitsample]
    
    def write_hitcircle_params(self, params):
        return self.HITCIRCLE_TYPES.write(params)
    
    def parse_spinner_params(self, raw_params):
        return self.SPINNER_TYPES.parse(raw_params)
    
    def write_spinner_params(self, params):
        return self.SPINNER_TYPES.write(params)

    def parse_hold_params(self, raw_params):
        endtime,_,sample = raw_params[0].partition(':')
        return self.HOLD_ENDTIME_TYPE.parse(endtime), self.parse_hitsample(sample)
    
    def write_hold_params(self, params):
        endtime = self.HOLD_ENDTIME_TYPE.write(params[0])
        sample = self.write_hitsample(params[1])
        return [endtime + ':' + sample]
    
    def parse_slider_params(self, raw_params):
        def fillexact(arr, size, obj):
            if len(arr) < size:
                arr.extend([obj] * (size-len(arr)))
            elif len(arr) > size:
                del arr[size:]
        
        (curvetype,curvepoints),repeats,length,edgesounds,edgesets,sample = self.SLIDER_TYPES.parse(raw_params)
        
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

    def parse_timingpoint_section(self, section, lines):
        def objs():
            for line in lines:
                try:
                    yield self.parse_timingpoint(line)
                except Exception as ex:
                    raise ValueError(f"failed to parse timing point {line!r}") from ex
        return list(filter(lambda tp: tp is not None, objs()))

    def write_timingpoint_section(self, file, section, section_data):
        for tp in section_data:
            file.write(self.write_timingpoint(tp) + '\n')
        
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

# ---------------------------------
#   Other stuff
# ---------------------------------
    def init_metadata_lookup_tables(self):
        osu_int = self.osu_int
        osu_float = self.osu_float
        osu_bool = self.osu_bool
        self.METADATA_TYPES = {
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