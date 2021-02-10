import unittest 
import osufile
from io import StringIO
from pathlib import Path
from inspect import cleandoc
from .SectionTest import SectionTest

class HitObjectsSectionTest(SectionTest):
    def setUp(self):
        base = osufile.Parser()
        parser = osufile.sections.HitObjects(base)
        super().setUp('HitObjects', parser)

    def test_empty_line(self):
        self._test_section(cleandoc('''
            200,100,10000,1,0,0:0:0:0:
            
            300,100,15000,1,0,0:0:0:0:
        '''), [
            osufile.HitCircle(x=200, y=100, time=10000, type=1, sound=0, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename='')),
            osufile.HitCircle(x=300, y=100, time=15000, type=1, sound=0, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))
        ])

#---------------------------------------------------------
#   HitSample tests
#--------------------------------------------------------- 
    def _get_sample_parser(self):
        return self.parser

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
#   HitObject tests
#---------------------------------------------------------
    def test_hitobject_header_not_enough_arguments(self):
        self._test_section_fail('200,100,10000,1')
    
    def test_hitobject_header_invalid(self):
        self._test_section_fail(cleandoc('''
            sdfdfg
            200,100,10000,1,0,0:0:0:0:
        '''))
    
    def test_hitobject_header_bad_input(self):
        self._test_section_fail(cleandoc('''
            200,100,10000,1,0,0:0:0:0:
            200,100,asdf,1,0,0:0:0:0:
        '''))
    
#---------------------------------------------------------
#   HitCircle tests
#---------------------------------------------------------
    def test_hitcircle(self):
        self._test_section(
            '200,100,10000,1,0,0:0:0:0:',
            [osufile.HitCircle(x=200, y=100, time=10000, type=1, sound=0, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )
    
    def test_hitcircle_extra_arguments(self):
        self._test_section(
            '200,100,10000,1,0,0:0:0:0:,asdfasdf',
            [osufile.HitCircle(x=200, y=100, time=10000, type=1, sound=0, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )

    def test_hitcircle_missing_sample(self):
        self._test_section(
            '200,100,10000,1,0',
            [osufile.HitCircle(x=200, y=100, time=10000, type=1, sound=0, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )

    def test_hitcircle_empty_sample(self):
        self._test_section(
            '200,100,10000,1,0,',
            [osufile.HitCircle(x=200, y=100, time=10000, type=1, sound=0, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )
        
    def test_hitcircle_roundtrip(self):
        self._test_roundtrip(cleandoc('''
            200,100,10000,1,0
            200,100,20000,1,0,0:0:0:0:
        '''))

#---------------------------------------------------------
#   Hold note tests
#---------------------------------------------------------
    def test_holdnote(self):
        self._test_section(
            '200,100,10000,128,0,11000:1:2:3:4:',
            [osufile.Hold(x=200, y=100, time=10000, type=128, sound=0, endtime=11000, sample=osufile.HitSample(normal_set=1, addition_set=2, index=3, volume=4, filename=''))]
        )
    
    def test_holdnote_missing_sample(self):
        self._test_section_fail('200,100,10000,128,0')
    
    def test_holdnote_bad_arguments(self):
        self._test_section_fail('200,100,10000,128,0,asdf:1:2:3:4:')
    
    def test_holdnote_extra_arguments(self):
        self._test_section(
            '200,100,10000,128,0,11000:1:2:3:4::hi',
            [osufile.Hold(x=200, y=100, time=10000, type=128, sound=0, endtime=11000, sample=osufile.HitSample(normal_set=1, addition_set=2, index=3, volume=4, filename=''))]
        )

    def test_holdnote_roundtrip(self):
        self._test_roundtrip(cleandoc('''
            200,100,10000,128,0,11000:1:2:3:4:
        '''))

#---------------------------------------------------------
#   Spinner tests
#---------------------------------------------------------
    def test_spinner(self):
        self._test_section(
            '256,192,5000,12,0,6000,0:0:0:0:',
            [osufile.Spinner(x=256, y=192, time=5000, type=12, sound=0, endtime=6000, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )
    
    def test_spinner_missing_arguments(self):
        self._test_section_fail('256,192,5000,12,0,6000')     # missing hit sample
        self._test_section_fail('256,192,5000,12,0')          # missing endtime
        self._test_section_fail('256,192,5000,12,0,')         # empty endtime
        self._test_section_fail('256,192,5000,12,0,6000,')    # empty hit sample

    def test_spinner_bad_arguments(self):
        self._test_section_fail('256,192,5000,12,asdf,0:0:0:0:')
    
    def test_spinner_extra_arguments(self):
        self._test_section(
            '256,192,5000,12,0,6000,0:0:0:0:,14',
            [osufile.Spinner(x=256, y=192, time=5000, type=12, sound=0, endtime=6000, sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )
    
    def test_spinner_roundtrip(self):
        self._test_roundtrip(cleandoc('''
            256,192,5000,12,0,6000,0:0:0:0:
        ''')) 

#---------------------------------------------------------
#   Slider tests
#---------------------------------------------------------    
    def test_slider(self):
        self._test_section(
            '442,316,10170,2,0,P|459:276|452:220,1,83.9999974365235,2|0,0:0|0:0,0:0:0:0:',
            [osufile.Slider(x=442, y=316, time=10170, type=2, sound=0, curvetype='P', curvepoints=[(459, 276), (452, 220)], slides=1, length=83.9999974365235, edgesounds=[2, 0], edgesets=[(0, 0), (0, 0)], sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )
        self._test_section(
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
            self._test_section(s, [e])
        # self.assertEqual(self.parse_hitobjects('\n'.join(sliders)), EXPECTED)

    def test_slider_too_few_arguments(self):
        self._test_section_fail('56,7,11670,2,0,L|152:-2')

    def test_slider_too_many_arguments(self):
        self._test_section(
            '56,7,11670,2,0,L|152:-2,1,83.9999974365235,0,0:0,0:0:0:0:,hi',
            [osufile.Slider(x=56, y=7, time=11670, type=2, sound=0, curvetype='L', curvepoints=[(152, -2)], slides=1, length=83.9999974365235, edgesounds=[0], edgesets=[(0, 0)], sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        )
    
    def test_slider_edgesounds(self):
        expected = [osufile.Slider(x=343, y=300, time=12570, type=2, sound=0, curvetype='P', curvepoints=[(308, 266), (266, 254)], slides=1, length=83.9999974365235, edgesounds=[2, 0], edgesets=[(2, 2), (0, 0)], sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        check = lambda x: self._test_section(x, expected)
        
        # extra pipes (ignored)
        check('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0|5,2:2|0:0,0:0:0:0:')
        # missing pipes (should be filled with 0)
        check('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2,2:2|0:0,0:0:0:0:')
        # invalid pipes (should be filled with 0)
        check('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|asdf,2:2|0:0,0:0:0:0:')
    
    def test_slider_edgesets(self):
        expected = [osufile.Slider(x=343, y=300, time=12570, type=2, sound=0, curvetype='P', curvepoints=[(308, 266), (266, 254)], slides=1, length=83.9999974365235, edgesounds=[2, 0], edgesets=[(2, 2), (0, 0)], sample=osufile.HitSample(normal_set=0, addition_set=0, index=0, volume=0, filename=''))]
        check = lambda x: self._test_section(x, expected)

        # extra pipes (ignored)
        check('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0,2:2|0:0|3:4,0:0:0:0:')
        # missing pipes (should be filled with (0,0))
        check('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0,2:2,0:0:0:0:')
        # invalid arguments in pipes (error)
        self._test_section_fail('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0,2:2|ohno,0:0:0:0:')
        # extra colons (ignored)
        check('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0,2:2:4|0:0:1|3:4:0,0:0:0:0:')
        # missing colons (error)
        self._test_section_fail('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0,2|0,0:0:0:0:')
        # invalid arguments in colons (error)
        self._test_section_fail('343,300,12570,2,0,P|308:266|266:254,1,83.9999974365235,2|0,2:2|0:ohno,0:0:0:0:')
    
    def test_slider_roundtrip(self):
        self._test_roundtrip(cleandoc('''
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

        for (objtype, expected) in test_cases.items():
            self.assertEqual(self.parser.hitobject_whattype(objtype), expected)