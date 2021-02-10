import unittest 
import osufile
from io import StringIO
from pathlib import Path
from inspect import cleandoc
from .SectionTest import SectionTest

class TimingPointsSectionTest(SectionTest):
    def setUp(self):
        base = osufile.Parser()
        parser = osufile.sections.TimingPoints(base)
        super().setUp('TimingPoints', parser)

    def test_timingpoint(self):
        sample = '0,300,4,1,0,100,1,0\n1000,-75,4,2,0,50,0,0'
        self._test_section(sample, [
            osufile.TimingPoint(time=0, tick=300.0, meter=4, sampleset=1, sampleindex=0, volume=100, uninherited=True, effects=0), 
            osufile.TimingPoint(time=1000, tick=-75.0, meter=4, sampleset=2, sampleindex=0, volume=50, uninherited=False, effects=0)
        ])

    def test_timingpoint_empty(self):
        self._test_section('', [])
        self._test_section('\n\n', [])

    def test_timingpoint_bad_input(self):
        # bad timing points are ignored
        sample = cleandoc('''
        kjkjkjkjkjkjk
        0,300,4,1,0,100,1,0

        500,1,34wwerw
        90e00,e,5,t
        a,s,d,f
        ''')
        EXPECTED = [
            osufile.TimingPoint(time=0, tick=300.0, meter=4, sampleset=1, sampleindex=0, volume=100, uninherited=True, effects=0)
        ]
        self._test_section(sample, EXPECTED)
    
    def test_timingpoint_optional_arguments(self):
        sample = cleandoc('''
        0,300,4,1,0,100,1,0
        0,300,4,1,0,100,1
        0,300,4,1,0,100
        0,300,4,1,0
        0,300,4,1
        ''')
        EXPECTED = [
            osufile.TimingPoint(time=0, tick=300.0, meter=4, sampleset=1, sampleindex=0, volume=100, uninherited=True, effects=0)
        ] * 5
        self._test_section(sample, EXPECTED)
    
    def test_timingpoint_too_few_arguments(self):
        self._test_section_fail('0,300,4')
    
    def test_timingpoint_too_many_arguments(self):
        sample = cleandoc('''
        0,300,4,1,0,100,1,0,50
        0,300,4,1,0,100,1,0,50,asdf
        ''')
        EXPECTED = [
            osufile.TimingPoint(time=0, tick=300.0, meter=4, sampleset=1, sampleindex=0, volume=100, uninherited=True, effects=0)
        ] * 2
        self._test_section(sample, EXPECTED)
        
    def test_timingpoint_out_of_order(self):
        # could sort them by time if they're out of order, but for now, don't bother sorting them
        sample = cleandoc('''
        0,300,4,1,0,100,1,0
        2000,-75,4,2,0,50,0,0
        1000,-75,4,2,0,50,0,0
        ''')
        EXPECTED = [
            osufile.TimingPoint(time=0, tick=300.0, meter=4, sampleset=1, sampleindex=0, volume=100, uninherited=True, effects=0), 
            osufile.TimingPoint(time=2000, tick=-75.0, meter=4, sampleset=2, sampleindex=0, volume=50, uninherited=False, effects=0),
            osufile.TimingPoint(time=1000, tick=-75.0, meter=4, sampleset=2, sampleindex=0, volume=50, uninherited=False, effects=0)
        ]
        self._test_section(sample, EXPECTED)
    
    def test_timingpoint_roundtrip(self):
        sample = cleandoc('''
        0,300,4,1,0,100,1,0
        2000,-75,4,2,0,50,0,0
        1000,-75,4,2,0,50,0,0
        ''')
        self._test_roundtrip(sample)
    