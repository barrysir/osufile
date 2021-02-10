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
    
    def parse_hitobjects(self, hitobjs):
        '''Parse some hitobjects'''
        # create an osu file with only hitobjects and pass it into the parser
        sample = (
            'osu file format v14\n'
            '\n'
            '[HitObjects]\n'
            f'{hitobjs}'
        )
        osu = self.parse_string(sample)
        return osu['HitObjects']

    def _test_hitobjects(self, hitobjs, expected):
        self.assertEqual(self.parse_hitobjects(hitobjs), expected)
    
    def _test_hitobject_fail(self, hitobjs):
        with self.assertRaises(Exception):
            self.parse_hitobjects(hitobjs)
        
    def _test_hitobject_roundtrip(self, hitobjs):
        sample = (
            'osu file format v14\n'
            '\n'
            '[HitObjects]\n'
            f'{hitobjs}'
        )
        self.roundtrip(sample)


#---------------------------------------------------------
#   HitObject tests
#---------------------------------------------------------
    def test_hitobject_header_not_enough_arguments(self):
        self._test_hitobject_fail('200,100,10000,1')
    
    def test_hitobject_header_invalid(self):
        self._test_hitobject_fail(cleandoc('''
            sdfdfg
            200,100,10000,1,0,0:0:0:0:
        '''))
    
    def test_hitobject_header_bad_input(self):
        self._test_hitobject_fail(cleandoc('''
            200,100,10000,1,0,0:0:0:0:
            200,100,asdf,1,0,0:0:0:0:
        '''))
    
#---------------------------------------------------------
#   HitCircle tests
#---------------------------------------------------------
    def test_hitcircle(self):
        self._test_hitobjects(
            '200,100,10000,1,0,0:0:0:0:',
            [osufile.HitCircle(x=200, y=100, time=10000, type=1, sound=0, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )
    
    def test_hitcircle_extra_arguments(self):
        self._test_hitobjects(
            '200,100,10000,1,0,0:0:0:0:,asdfasdf',
            [osufile.HitCircle(x=200, y=100, time=10000, type=1, sound=0, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )

    def test_hitcircle_missing_sample(self):
        self._test_hitobjects(
            '200,100,10000,1,0',
            [osufile.HitCircle(x=200, y=100, time=10000, type=1, sound=0, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )

    def test_hitcircle_empty_sample(self):
        self._test_hitobjects(
            '200,100,10000,1,0,',
            [osufile.HitCircle(x=200, y=100, time=10000, type=1, sound=0, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )
        
    def test_hitcircle_roundtrip(self):
        self._test_hitobject_roundtrip(cleandoc('''
            200,100,10000,1,0
            200,100,20000,1,0,0:0:0:0:
        '''))

#---------------------------------------------------------
#   HitSample tests
#--------------------------------------------------------- 
    def _get_sample_parser(self):
        return osufile.sections.HitObjects(osufile.Parser())

    def test_hitsample(self):
        sample = '1:2:3:4:hi.wav'
        EXPECTED = osufile.HitSample(normal_set=1, addition_set=2, index=3, volume=4, filename='hi.wav')
        actual = self._get_sample_parser().parse_hitsample(sample)
        self.assertEqual(actual, EXPECTED)
    
    def test_hitsample_extra_arguments(self):
        sample = '1:2:3:4:hi.wav:adsfasdf'
        EXPECTED = osufile.HitSample(normal_set=1, addition_set=2, index=3, volume=4, filename='hi.wav')
        actual = self._get_sample_parser().parse_hitsample(sample)
        self.assertEqual(actual, EXPECTED)
    
    def test_hitsample_missing_arguments(self):
        sample = '1:2:3'
        with self.assertRaises(Exception):
            self._get_sample_parser().parse_hitsample(sample)

#---------------------------------------------------------
#   Hold note tests
#---------------------------------------------------------
    def test_holdnote(self):
        self._test_hitobjects(
            '200,100,10000,128,0,11000:1:2:3:4:',
            [osufile.Hold(x=200, y=100, time=10000, type=128, sound=0, endtime=11000, sample=osufile.HitSample(normal_set=1, addition_set=2, index=3, volume=4, filename=''))]
        )
    
    def test_holdnote_missing_sample(self):
        self._test_hitobject_fail('200,100,10000,128,0')
    
    def test_holdnote_bad_arguments(self):
        self._test_hitobject_fail('200,100,10000,128,0,asdf:1:2:3:4:')
    
    def test_holdnote_extra_arguments(self):
        self._test_hitobjects(
            '200,100,10000,128,0,11000:1:2:3:4::hi',
            [osufile.Hold(x=200, y=100, time=10000, type=128, sound=0, endtime=11000, sample=osufile.HitSample(normal_set=1, addition_set=2, index=3, volume=4, filename=''))]
        )

    def test_holdnote_roundtrip(self):
        self._test_hitobject_roundtrip(cleandoc('''
            200,100,10000,128,0,11000:1:2:3:4:
        '''))

#---------------------------------------------------------
#   Spinner tests
#---------------------------------------------------------
    def test_spinner(self):
        self._test_hitobjects(
            '256,192,5000,12,0,6000,0:0:0:0:',
            [osufile.Spinner(x=256, y=192, time=5000, type=12, sound=0, endtime=6000, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )
    
    def test_spinner_missing_arguments(self):
        self._test_hitobject_fail('256,192,5000,12,0,6000')     # missing hit sample
        self._test_hitobject_fail('256,192,5000,12,0')          # missing endtime
        self._test_hitobject_fail('256,192,5000,12,0,')         # empty endtime
        self._test_hitobject_fail('256,192,5000,12,0,6000,')    # empty hit sample

    def test_spinner_bad_arguments(self):
        self._test_hitobject_fail('256,192,5000,12,asdf,0:0:0:0:')
    
    def test_spinner_extra_arguments(self):
        self._test_hitobjects(
            '256,192,5000,12,0,6000,0:0:0:0:,14',
            [osufile.Spinner(x=256, y=192, time=5000, type=12, sound=0, endtime=6000, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )
    
    def test_spinner_roundtrip(self):
        self._test_hitobject_roundtrip(cleandoc('''
            256,192,5000,12,0,6000,0:0:0:0:
        ''')) 

#---------------------------------------------------------
#   Slider tests
#---------------------------------------------------------    
    def test_slider(self):
        self._test_hitobjects(
            '442,316,10170,2,0,P|459:276|452:220,1,83.9999974365235,2|0,0:0|0:0,0:0:0:0:',
            [osufile.Slider(x=442, y=316, time=10170, type=2, sound=0, curvetype='P', curvepoints=[(459, 276), (452, 220)], slides=1, length=83.9999974365235, edgesounds=[2, 0], edgesets=[(0, 0), (0, 0)], sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )
        self._test_hitobjects(
            '56,7,11670,2,0,L|152:-2,1,83.9999974365235,0,0:0,0:0:0:0:',
            [osufile.Slider(x=56, y=7, time=11670, type=2, sound=0, curvetype='L', curvepoints=[(152, -2)], slides=1, length=83.9999974365235, edgesounds=[0], edgesets=[(0, 0)], sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )

    def test_slider_optional_arguments(self):
        sliders = [
            '56,7,11670,2,0,L|152:-2,1,83.9999974365235,0,0:0,0:0:0:0:',
            '56,7,11670,2,0,L|152:-2,1,83.9999974365235,0,0:0',
            '56,7,11670,2,0,L|152:-2,1,83.9999974365235,0',
            '56,7,11670,2,0,L|152:-2,1,83.9999974365235',
            '56,7,11670,2,0,L|152:-2,1'
        ]
        EXPECTED = [
            osufile.Slider(x=56, y=7, time=11670, type=2, sound=0, curvetype='L', curvepoints=[(152, -2)], slides=1, length=83.9999974365235, edgesounds=[0], edgesets=[(0, 0)], sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))
        for i in range(len(sliders))]

        # the parser doesn't recalculate omitted lengths, it sets the lengths to 0,
        # so for all sliders with omitted lengths we'll set the expected data to 0
        for i in range(4, len(EXPECTED)):
            EXPECTED[i].length = 0

        for s,e in zip(sliders, EXPECTED):
            self._test_hitobjects(s, [e])
        # self.assertEqual(self.parse_hitobjects('\n'.join(sliders)), EXPECTED)

    def test_slider_too_few_arguments(self):
        self._test_hitobject_fail('56,7,11670,2,0,L|152:-2')

    def test_slider_too_many_arguments(self):
        self._test_hitobjects(
            '56,7,11670,2,0,L|152:-2,1,83.9999974365235,0,0:0,0:0:0:0:,hi',
            [osufile.Slider(x=56, y=7, time=11670, type=2, sound=0, curvetype='L', curvepoints=[(152, -2)], slides=1, length=83.9999974365235, edgesounds=[0], edgesets=[(0, 0)], sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )
    
    def test_slider_edgesounds(self):
        expected = [osufile.Slider(x=343, y=300, time=12570, type=2, sound=0, curvetype='P', curvepoints=[(308, 266), (266, 254)], slides=1, length=83.9999974365235, edgesounds=[2, 0], edgesets=[(2, 2), (0, 0)], sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        check = lambda x: self._test_hitobjects(x, expected)
        
        # extra pipes (ignored)
        check('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0|5,2:2|0:0,0:0:0:0:')
        # missing pipes (should be filled with 0)
        check('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2,2:2|0:0,0:0:0:0:')
        # invalid pipes (should be filled with 0)
        check('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|asdf,2:2|0:0,0:0:0:0:')
    
    def test_slider_edgesets(self):
        expected = [osufile.Slider(x=343, y=300, time=12570, type=2, sound=0, curvetype='P', curvepoints=[(308, 266), (266, 254)], slides=1, length=83.9999974365235, edgesounds=[2, 0], edgesets=[(2, 2), (0, 0)], sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        check = lambda x: self._test_hitobjects(x, expected)

        # extra pipes (ignored)
        check('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0,2:2|0:0|3:4,0:0:0:0:')
        # missing pipes (should be filled with (0,0))
        check('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0,2:2,0:0:0:0:')
        # invalid arguments in pipes (error)
        self._test_hitobject_fail('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0,2:2|ohno,0:0:0:0:')
        # extra colons (ignored)
        check('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0,2:2:4|0:0:1|3:4:0,0:0:0:0:')
        # missing colons (error)
        self._test_hitobject_fail('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0,2|0,0:0:0:0:')
        # invalid arguments in colons (error)
        self._test_hitobject_fail('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0,2:2|0:ohno,0:0:0:0:')
    
    def test_slider_roundtrip(self):
        self._test_hitobject_roundtrip(cleandoc('''
            442,316,10170,2,0,P|459:276|452:220,1,83.9999974365235,2|0,0:0|0:0,0:0:0:0:
            56,7,11670,2,0,L|152:-2,1,83.9999974365235,0,0:0,0:0:0:0:
            343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0,2:2|0:0,0:0:0:0:
        '''))

#---------------------------------------------------------
#   Bit precedence
#---------------------------------------------------------   
    def test_hitobject_precedence(self):
        CIRCLE    = 0b00000001
        SLIDER    = 0b00000010
        SPINNER   = 0b00001000
        HOLD      = 0b10000000

        test_cases = {
            # the obvious cases
            CIRCLE: CIRCLE,
            SLIDER: SLIDER,
            SPINNER: SPINNER,
            HOLD: HOLD,
            # mixups
            CIRCLE|SLIDER: CIRCLE,
            CIRCLE|SPINNER: CIRCLE,
            CIRCLE|HOLD: CIRCLE,
            SLIDER|SPINNER: SLIDER,
            SLIDER|HOLD: SLIDER,
            SPINNER|HOLD: SPINNER,
            # none
            0: None,
        }

        hitobjs = osufile.sections.HitObjects(osufile.Parser())
        for (objtype, expected) in test_cases.items():
            self.assertEqual(hitobjs.hitobject_whattype(objtype), expected)