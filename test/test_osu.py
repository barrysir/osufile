import unittest 
import osufile
from io import StringIO
from pathlib import Path
from inspect import cleandoc

__CWD__ = Path(__file__).parent.absolute()

# metadata behaviour
# invalid tags are ignored
# invalid types for metadata crashes the parser (AudioLeadIn: asdf)
# extra tags don't affect parsing
# multiple definitions of the same data
#  Title: Title1
#  Title: Title2        <- this one takes precedence

# timing point behaviour
# timing points with garbage values are ignored
# how many timing point arguments are necessary?
#       sampleset: crashes parser
#       sampleindex: 0
#       volume: 100
#       kiai: False
#       uninherited: False
# extra arguments?
#       ignored
# timing points out of order are sorted
#       don't do it with this parser?

# hit objects
# lost arguments?
#   hit objects with fewer arguments than the header (x,y,time,type,hitsound) crashes the parser
# extra arguments?
#   extra arguments are ignored
# which bits take precedence in determining what kind of hit object it is?
# invalid inputs cause parser to crash
# ... except if the invalid input is the first object, then the file will load correctly (but osu will complain)
# if any text is put after [HitObjects] (including spaces), the parser throws an error

# hit samples
# default is 0:0:0:0:
# if hit sample is '', returns default
# all arguments must be present
# extra arguments are ignored

# osumania holds
# argument is mandatory (it doesn't crash, but it causes the file to glitch out)
# all parameters are mandatory
# extra arguments are ignored

# sliders
# length is optional
# edgesounds is optional    (default: probably 0?)
#    extra pipes are ignored
#    missing pipes are filled (filled with 0)
#    invalid arguments are treated as 0
# edgesets is optional      (default: probably 0?)
#    extra pipes are ignored
#    missing pipes are filled (filled with 0:0)
#    extra colons are ignored
#    missing colons throw an error
#    invalid arguments throw an error
# sample is optional        (default: 0:0:0:0:)
#    extra colons are ignored
# extra arguments are ignored
# if edgesounds,edgesets,sample is all 0s, then the data is not saved by osu (to save space)

# // comments...
# are probably not an actual thing, but a side-effect of invalid inputs being ignored
# are not parsed out of values       (AudioLeadIn: 0 //test, Title: PLANET // SHAPER)
# are only removed if they begin a line
#    Title:title1
#    Title //:title2
# has no effect


class OsuFileTest(unittest.TestCase):
    def roundtrip(self, sample):
        '''Run a roundtrip test on an .osu file (parse string -> write string -> parse string again -> check that first and second parse are the same)'''
        if isinstance(sample, osufile.OsuFile):
            expected_osu = sample
        elif isinstance(sample, str):
            expected_osu = self.parse_string(sample)
        else:
            expected_osu = osufile.parse(sample)
        
        output = StringIO()
        osufile.write(output, expected_osu)
        output.seek(0)
        actual_osu = osufile.parse(output)
        self.assertEqual(expected_osu, actual_osu)

    def parse_string(self, s):
        '''Parse .osu file held as contents of string'''
        return osufile.parse(StringIO(s))
    
    def write_string(self, osu):
        s = StringIO()
        osufile.write(s, osu)
        return s.getvalue()