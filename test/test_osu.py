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

# // comments...
# are probably not an actual thing, but a side-effect of invalid inputs being ignored
# are not parsed out of values       (AudioLeadIn: 0 //test, Title: PLANET // SHAPER)
# are only removed if they begin a line
#    Title:title1
#    Title //:title2
# has no effect


class OsuFileTest(unittest.TestCase):
    def roundtrip(self, sample):
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
        return osufile.parse(StringIO(s))

#---------------------------------------------------------
#   Metadata tests
#---------------------------------------------------------
    def test_metadata_empty_section(self):
        sample = cleandoc('''
        osu file format v14
        [General]
        ''')
        osu = self.parse_string(sample)
        self.assertEqual(osu['General'], {})
    
    def test_metadata_unknown_tags(self):
        sample = cleandoc('''
        osu file format v14
        [General]
        AudioFilename: audio.mp3
        NewTag: hello
        ''')
        osu = self.parse_string(sample)
        self.assertEqual(osu['General'], {'AudioFilename': 'audio.mp3', 'NewTag': 'hello'})
    
    def test_metadata_roundtrip(self):
        sample = cleandoc('''
        osu file format v14
        [General]
        AudioFilename: audio.mp3
        NewTag: hello
        ''')
        self.roundtrip(sample)
    
    def test_metadata_ignore_invalid_tags(self):
        sample = cleandoc('''
        osu file format v14

        [General]
        AudioFilename: audio.mp3

        badtag
        o0o0o0o0o    
        ''')
        osu = self.parse_string(sample)
        self.assertEqual(osu['General'], {'AudioFilename': 'audio.mp3'})
    
    def test_metadata_crash_invalid_tag_data(self):
        sample = cleandoc('''
        osu file format v14

        [General]
        AudioFilename: audio.mp3
        AudioLeadIn: asdf
        ''')
        with self.assertRaises(Exception):
            osu = self.parse_string(sample)
    
    def test_metadata_multiple_definitions(self):
        sample = cleandoc('''
        osu file format v14

        [General]
        AudioFilename: audio.mp3
        AudioFilename: audio2.mp3
        ''')
        osu = self.parse_string(sample)
        self.assertEqual(osu['General'], {'AudioFilename': 'audio2.mp3'})

#---------------------------------------------------------
#   TimingPoint tests
#---------------------------------------------------------
    def test_timingpoint(self):
        sample = cleandoc('''
        osu file format v14

        [TimingPoints]
        0,300,4,1,0,100,1,0
        1000,-75,4,2,0,50,0,0
        ''')
        osu = self.parse_string(sample)
        EXPECTED = [
            osufile.TimingPoint(time=0, tick=300.0, meter=4, sampleset=1, sampleindex=0, volume=100, uninherited=True, effects=0), 
            osufile.TimingPoint(time=1000, tick=-75.0, meter=4, sampleset=2, sampleindex=0, volume=50, uninherited=False, effects=0)
        ]
        self.assertEqual(osu['TimingPoints'], EXPECTED)
        self.roundtrip(sample)

    def test_timingpoint_empty(self):
        sample = cleandoc('''
        osu file format v14

        [TimingPoints]
        ''')
        osu = self.parse_string(sample)
        self.assertEqual(osu['TimingPoints'], [])

    def test_timingpoint_bad_input(self):
        sample = cleandoc('''
        osu file format v14

        [TimingPoints]
        kjkjkjkjkjkjk
        0,300,4,1,0,100,1,0

        500,1,34wwerw
        90e00,e,5,t
        a,s,d,f
        ''')
        osu = self.parse_string(sample)
        EXPECTED = [
            osufile.TimingPoint(time=0, tick=300.0, meter=4, sampleset=1, sampleindex=0, volume=100, uninherited=True, effects=0)
        ]
        self.assertEqual(osu['TimingPoints'], EXPECTED)
    
    def test_timingpoint_cutting_off_arguments(self):
        sample = cleandoc('''
        osu file format v14

        [TimingPoints]
        0,300,4,1,0,100,1,0
        0,300,4,1,0,100,1
        0,300,4,1,0,100
        0,300,4,1,0
        0,300,4,1
        ''')
        osu = self.parse_string(sample)
        EXPECTED = [
            osufile.TimingPoint(time=0, tick=300.0, meter=4, sampleset=1, sampleindex=0, volume=100, uninherited=True, effects=0)
        ] * 5
        self.assertEqual(osu['TimingPoints'], EXPECTED)
    
    def test_timingpoint_too_few_arguments(self):
        sample = cleandoc('''
        osu file format v14

        [TimingPoints]
        0,300,4
        ''')
        with self.assertRaises(Exception):
            osu = self.parse_string(sample)
    
    def test_timingpoint_too_many_arguments(self):
        sample = cleandoc('''
        osu file format v14

        [TimingPoints]
        0,300,4,1,0,100,1,0,50
        ''')
        osu = self.parse_string(sample)
        EXPECTED = [
            osufile.TimingPoint(time=0, tick=300.0, meter=4, sampleset=1, sampleindex=0, volume=100, uninherited=True, effects=0)
        ]
        self.assertEqual(osu['TimingPoints'], EXPECTED)
        
    def test_timingpoint_out_of_order(self):
        # for now, don't bother sorting them
        sample = cleandoc('''
        osu file format v14

        [TimingPoints]
        0,300,4,1,0,100,1,0
        2000,-75,4,2,0,50,0,0
        1000,-75,4,2,0,50,0,0
        ''')
        osu = self.parse_string(sample)
        EXPECTED = [
            osufile.TimingPoint(time=0, tick=300.0, meter=4, sampleset=1, sampleindex=0, volume=100, uninherited=True, effects=0), 
            osufile.TimingPoint(time=2000, tick=-75.0, meter=4, sampleset=2, sampleindex=0, volume=50, uninherited=False, effects=0),
            osufile.TimingPoint(time=1000, tick=-75.0, meter=4, sampleset=2, sampleindex=0, volume=50, uninherited=False, effects=0)
        ]
        self.assertEqual(osu['TimingPoints'], EXPECTED)
    
    def test_timingpoint_roundtrip(self):
        sample = cleandoc('''
        osu file format v14

        [TimingPoints]
        0,300,4,1,0,100,1,0
        2000,-75,4,2,0,50,0,0
        1000,-75,4,2,0,50,0,0
        ''')
        self.roundtrip(sample)
    
#---------------------------------------------------------
#   HitObject tests
#---------------------------------------------------------
    def test_hitobject_not_enough_arguments(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        200,100,10000,1
        ''')
        with self.assertRaises(Exception):
            osu = self.parse_string(sample)
    
    def test_hitobject_invalid(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        sdfdfg
        200,100,10000,1,0,0:0:0:0:
        ''')
        with self.assertRaises(Exception):
            osu = self.parse_string(sample)
    
    def test_hitobject_bad_input(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        200,100,10000,1,0,0:0:0:0:
        200,100,asdf,1,0,0:0:0:0:
        ''')
        with self.assertRaises(Exception):
            osu = self.parse_string(sample)
        
    def test_hitobject_roundtrip(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        200,100,10000,1,0
        200,100,20000,1,0,0:0:0:0:
        200,100,10000,128,0,11000:1:2:3:4:
        ''')
        self.roundtrip(sample)
    
#---------------------------------------------------------
#   HitCircle tests
#---------------------------------------------------------
    def test_hitcircle(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        200,100,10000,1,0,0:0:0:0:
        ''')
        osu = self.parse_string(sample)
        EXPECTED = [
            osufile.HitCircle(x=200, y=100, time=10000, type=1, sound=0, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))
        ]
        self.assertEqual(osu['HitObjects'], EXPECTED)
    
    def test_hitcircle_extra_arguments(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        200,100,10000,1,0,0:0:0:0:,4
        ''')
        osu = self.parse_string(sample)
        EXPECTED = [
            osufile.HitCircle(x=200, y=100, time=10000, type=1, sound=0, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))
        ]
        self.assertEqual(osu['HitObjects'], EXPECTED)

    def test_hitcircle_missing_sample(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        200,100,10000,1,0
        ''')
        osu = self.parse_string(sample)
        EXPECTED = [
            osufile.HitCircle(x=200, y=100, time=10000, type=1, sound=0, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))
        ]
        self.assertEqual(osu['HitObjects'], EXPECTED)

    def test_hitcircle_empty_sample(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        200,100,10000,1,0,
        ''')
        osu = self.parse_string(sample)
        EXPECTED = [
            osufile.HitCircle(x=200, y=100, time=10000, type=1, sound=0, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))
        ]
        self.assertEqual(osu['HitObjects'], EXPECTED)

#---------------------------------------------------------
#   HitSample tests
#---------------------------------------------------------
    def test_hitsample(self):
        sample = '1:2:3:4:hi.wav'
        EXPECTED = osufile.HitSample(normal_set=1, addition_set=2, index=3, volume=4, filename='hi.wav')
        actual = osufile.Parser().parse_hitsample(sample)
        self.assertEqual(actual, EXPECTED)
    
    def test_hitsample_extra_arguments(self):
        sample = '1:2:3:4:hi.wav:adsfasdf'
        EXPECTED = osufile.HitSample(normal_set=1, addition_set=2, index=3, volume=4, filename='hi.wav')
        actual = osufile.Parser().parse_hitsample(sample)
        self.assertEqual(actual, EXPECTED)
    
    def test_hitsample_missing_arguments(self):
        sample = '1:2:3'
        with self.assertRaises(Exception):
            osufile.Parser().parse_hitsample(sample)

#---------------------------------------------------------
#   Hold note tests
#---------------------------------------------------------
    def test_holdnote(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        200,100,10000,128,0,11000:1:2:3:4:
        ''')
        osu = self.parse_string(sample)
        EXPECTED = [
            osufile.Hold(x=200, y=100, time=10000, type=128, sound=0, endtime=11000, sample=osufile.HitSample(normal_set=1, addition_set=2, index=3, volume=4, filename=''))
        ]
        self.assertEqual(osu['HitObjects'], EXPECTED)
    
    def test_holdnote_missing_sample(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        200,100,10000,128,0
        ''')
        with self.assertRaises(Exception):
            osu = self.parse_string(sample)
    
    def test_holdnote_bad_arguments(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        200,100,10000,128,0,asdf:1:2:3:4:
        ''')
        with self.assertRaises(Exception):
            osu = self.parse_string(sample)
    
    def test_holdnote_extra_arguments(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        200,100,10000,128,0,11000:1:2:3:4::hi
        ''')
        osu = self.parse_string(sample)
        EXPECTED = [
            osufile.Hold(x=200, y=100, time=10000, type=128, sound=0, endtime=11000, sample=osufile.HitSample(normal_set=1, addition_set=2, index=3, volume=4, filename=''))
        ]
        self.assertEqual(osu['HitObjects'], EXPECTED)

#---------------------------------------------------------
#   Spinner tests
#---------------------------------------------------------
    def test_spinner(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        256,192,5000,12,0,6000,0:0:0:0:
        ''')
        osu = self.parse_string(sample)
        EXPECTED = [
            osufile.Spinner(x=256, y=192, time=5000, type=12, sound=0, endtime=6000, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))
        ]
        self.assertEqual(osu['HitObjects'], EXPECTED)
    
    def test_spinner_missing_arguments(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        256,192,5000,12,0,6000
        ''')
        with self.assertRaises(Exception):
            osu = self.parse_string(sample)

        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        256,192,5000,12,0
        ''')
        with self.assertRaises(Exception):
            osu = self.parse_string(sample)

        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        256,192,5000,12,0,
        ''')
        with self.assertRaises(Exception):
            osu = self.parse_string(sample)

    def test_spinner_bad_arguments(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        256,192,5000,12,asdf,0:0:0:0:
        ''')
        with self.assertRaises(Exception):
            osu = self.parse_string(sample)
    
    def test_spinner_extra_arguments(self):
        sample = cleandoc('''
        osu file format v14

        [HitObjects]
        256,192,5000,12,0,6000,0:0:0:0:,14
        ''')
        osu = self.parse_string(sample)
        EXPECTED = [
            osufile.Spinner(x=256, y=192, time=5000, type=12, sound=0, endtime=6000, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))
        ]
        self.assertEqual(osu['HitObjects'], EXPECTED)