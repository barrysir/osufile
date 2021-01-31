import collections
import itertools
from typing import TextIO

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

# namedtuple to store a parsing/writing function if you wanna use it
ParserPair = collections.namedtuple('ParserPair', ['parse', 'write'])

# --- Data types ---
class OsuFile(collections.OrderedDict):
    header: str

# --- Parser ---
class Parser:
    parse_bool = lambda x: bool(int(x))
    write_bool = lambda x: str(int(x))
    parse_int = lambda x: int(round(float(x)))
    write_int = lambda x: str(int(x))
    parse_float = float
    write_float = str

    def __init__(self):
        self.METADATA_TYPES = self.create_metadata_lookup_table()

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
                valid_metadata = filter(lambda kv: kv[0] is not None, (self.parse_metadata(section, line) for line in lines))
                osu[section] = {key:val for key,val in valid_metadata}
            elif section in {'HitObjects', 'TimingPoints', 'Events'}:
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
                for keyval in section.items():
                    file.write('{}\n'.format(self.write_metadata(section, keyval)))
            elif section in {'HitObjects', 'TimingPoints', 'Events'}:
                for obj in section:
                    file.write(','.join(obj) + '\n')
            else:
                for line in osu[section]:
                    file.write(line + '\n')
    
    # --- Metadata sections ---
    def parse_metadata(self, section: str, line: str) -> (str, any):
        key,hasSeparator,val = line.partition(':')
        if not hasSeparator:
            return (None, None)
        key = key.strip()
        val = self.lookup_metadata_parser(section, key).parse(val.strip())
        return (key,val)
    
    def write_metadata(self, section: str, keyval: (str, any)) -> str:
        key,val = keyval
        val = self.lookup_metadata_parser(section, key).write(val)
        return '{}:{}'.format(key, val)

    def lookup_metadata_parser(self, section: str, key: str) -> ParserPair:
        cls = self.__class__
        return self.METADATA_TYPES[section].get(key, ParserPair(str, str))

    # --- Hit objects ---

    # --- Timing points ---
    def parse_timingpoint(self, line):
        pass

    def write_timingpoint(self, tp) -> str:
        return ""

    @classmethod
    def create_metadata_lookup_table(cls):
        osu_int = ParserPair(cls.parse_int, cls.write_int)
        osu_float = ParserPair(cls.parse_float, cls.write_float)
        osu_bool = ParserPair(cls.parse_bool, cls.write_bool)
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