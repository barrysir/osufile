from abc import ABC, abstractmethod
from .combinator import *
from .util import *
from .datatypes import *
import warnings
import collections

class Section(ABC):
    @abstractmethod
    def parse(self, section_name, lines):
        return

    @abstractmethod
    def write(self, file, section_name, data):
        return

#----------------------------------
#    Metadata
#----------------------------------
class Metadata(Section):
    def __init__(self, base, lookup_table):
        self.base = base
        self.METADATA_TYPES = lookup_table

    def parse(self, section, lines):
        def metadata():
            for line in lines:
                try:
                    yield self.parse_metadata(section, line)
                except Exception as ex: 
                    raise ValueError(f"failed to parse metadata {line!r}") from ex
        valid_metadata = filter(lambda kv: kv is not None, metadata())
        return collections.OrderedDict(valid_metadata)
    
    def write(self, file, section, section_data):
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
        return self.METADATA_TYPES.get(key, ParserPair(str, str))

#----------------------------------------------------
#    Default Metadata factories
#----------------------------------------------------
def make_metadata_sections(base, LOOKUP_TABLE):
    return {section_name: Metadata(base, LOOKUP_TABLE[section_name]) for section_name in LOOKUP_TABLE.keys()}

def make_default_metadata_sections(base):
    LOOKUP_TABLE = make_default_metadata_lookup_table(base)
    return make_metadata_sections(base, LOOKUP_TABLE)

def make_default_metadata_lookup_table(base):
    osu_int = base.osu_int
    osu_bool = base.osu_bool
    osu_float = base.osu_float
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

#----------------------------------
#    TimingPoints
#----------------------------------
class TimingPoints(Section):
    def __init__(self, base):
        self.base = base
        osu_int = self.base.osu_int
        osu_bool = self.base.osu_bool
        osu_float = self.base.osu_float
        self.TIMINGPOINT_PARSE_TYPE,self.TIMINGPOINT_WRITE_TYPE = unzipl([osu_int, osu_float, osu_int, osu_int, osu_int, osu_int, osu_bool, osu_int])

    def parse(self, section, lines):
        def objs():
            for line in lines:
                try:
                    yield self.parse_timingpoint(line)
                except Exception as ex:
                    raise ValueError(f"failed to parse timing point {line!r}") from ex
        return list(filter(lambda tp: tp is not None, objs()))

    def write(self, file, section, section_data):
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

#----------------------------------
#    HitObjects
#----------------------------------
class HitObjects(Section):
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

    def __init__(self, base):
        self.base = base

        # basic types
        osu_int = base.osu_int
        osu_float = base.osu_float
        osu_bool = base.osu_bool
        osu_str = base.osu_str

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

    # --- helper functions ---
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
    
    # --- main ---
    def parse(self, section, lines):
        def objs():
            for line in lines:
                line = line.strip()
                if line == '': continue
                try:
                    yield self.parse_hitobject(line)
                except Exception as ex:
                    raise ValueError(f"failed to parse hit object {line!r}") from ex
        return list(filter(lambda x: x is not None, objs()))

    def write(self, file, section, section_data):
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


#----------------------------------
#    Events
#----------------------------------
from enum import Enum, auto

class Events(Section):
    class Type(Enum):
        BACKGROUND = auto()
        VIDEO = auto()
        BREAK = auto()

    def __init__(self, base):
        self.base = base
        osu_int = self.base.osu_int
        osu_bool = self.base.osu_bool
        osu_float = self.base.osu_float
        osu_str = self.base.osu_str
        osu_quoted_str = ParserPair(lambda x: osu_str.parse(x.strip('"')), osu_str.write)

        self.HEADER_TYPES = [ParserPair(lambda x: osu_str.parse(x.strip()), osu_str.write)]
        self.HEADER_SIZE = len(self.HEADER_TYPES)
        self.HEADER = ptuple(self.HEADER_TYPES)

        self.EVENT_LOOKUP = {
            self.Type.BACKGROUND: (EventBackground, ptuple([osu_int, osu_quoted_str, osu_int, osu_int], optionals=[0,0])),
            self.Type.VIDEO:      (EventVideo, ptuple([osu_int, osu_quoted_str, osu_int, osu_int], optionals=[0,0])),
            self.Type.BREAK:      (EventBreak, ptuple([osu_int, osu_int])),
            None:                 (EventUnknown, ParserPair(lambda raw_others: [raw_others], lambda id: id)),
        }

    def whattype(self, objtype):
        '''
        Figure out what event this is
        returns one of [, None],
        None if the object does not match any of these types
        '''
        LOOKUP = {
            '0':     self.Type.BACKGROUND,
            '1':     self.Type.VIDEO,
            'Video': self.Type.VIDEO,
            '2':     self.Type.BREAK,
        }
        return LOOKUP.get(objtype, None)
    
    def parse_line(self, line):
        # split header/others
        tokens = line.split(',')
        raw_header,raw_others = tokens[:self.HEADER_SIZE], tokens[self.HEADER_SIZE:]
        header = self.HEADER.parse(raw_header)
        
        eventtype = self.whattype(header[0])
        constructor, pw = self.EVENT_LOOKUP[eventtype]
        others = pw.parse(raw_others)
        return constructor(*header, *others)

    def write_line(self, obj):
        # split data object into header/params
        objdata = astuple_nonrecursive(obj)
        header, others = objdata[:self.HEADER_SIZE], objdata[self.HEADER_SIZE:]

        # serialize params
        for (type, pw) in self.EVENT_LOOKUP.values():
            if isinstance(obj, type):
                raw_others = pw.write(others)
                break
        else:
            assert False, f"unsupported object of type {obj.__class__.__name__} passed to event writer {obj!r}"

        # serialize header
        raw_header = self.HEADER.write(header)
        # header and others might be different types (list vs. tuple)
        # so we'll use this way of concatenating iterables
        return ','.join([*raw_header, *raw_others])

    def parse(self, section, lines):
        def objs():
            for line in lines:
                line = line.strip()
                if line == '': continue
                if line.startswith('//'): continue
                try:
                    yield self.parse_line(line)
                except Exception as ex:
                    raise ValueError(f"failed to parse event {line!r}") from ex
        return list(filter(lambda tp: tp is not None, objs()))

    def write(self, file, section, section_data):
        for item in section_data:
            file.write(self.write_line(item) + '\n')