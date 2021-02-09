from typing import TextIO
from .datatypes import OsuFile
from .sections import Metadata, TimingPoints, HitObjects, Events, make_default_metadata_sections
from .combinator import ParserPair
from .util import spliton

class Parser:
    # base parsers
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

        # Place the base parsing functions in the main parser for now
        self.init_base_parser()
        base_parser = self

        self.sections = {
            **make_default_metadata_sections(base_parser),
            'HitObjects': HitObjects(base_parser),
            'TimingPoints': TimingPoints(base_parser),
            'Events': Events(base_parser),
        }
    
    def init_base_parser(self):
        self.osu_int = ParserPair(self.parse_int, self.write_int)
        self.osu_float = ParserPair(self.parse_float, self.write_float)
        self.osu_bool = ParserPair(self.parse_bool, self.write_bool)
        self.osu_str = ParserPair(str,str)

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
                
        osu = OsuFile()

        header = next(file).strip()
        osu.header = header

        for section,lines in sections(file):
            if section in self.sections:
                osu[section] = self.sections[section].parse(section, lines)
            else:
                osu.setdefault(section, list(lines))
        
        return osu

    def write(self, file: TextIO, osu: OsuFile) -> None:
        file.write('osu file format v14' + '\n')    # output is written in v14 format
        for section in osu.keys():
            file.write('\n')     #newline to make the formatting look good
            file.write(f'[{section}]\n')

            if section in self.sections:
                self.sections[section].write(file, section, osu[section])
            else:
                for line in osu[section]:
                    file.write(line + '\n')