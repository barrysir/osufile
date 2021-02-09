import unittest 
import osufile
from io import StringIO
from pathlib import Path
from inspect import cleandoc

class EventSectionTest(unittest.TestCase):
    # --- Helpers ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base = osufile.Parser()
        self.parser = osufile.sections.Events(base)

    def roundtrip(self, sample):
        '''Run a roundtrip test on an .osu file (parse string -> write string -> parse string again -> check that first and second parse are the same)'''
        if isinstance(sample, str):
            expected_osu = self.parse_string(sample)
        else:
            expected_osu = sample
        
        actual_osu = self.parse_string(self.write_string(expected_osu))
        self.assertEqual(expected_osu, actual_osu)
    
    def parse_string(self, events):
        return self.parser.parse('Events', events.split('\n'))
    
    def write_string(self, eventlist):
        s = StringIO()
        self.parser.write(s, 'Events', eventlist)
        return s.getvalue()

    def _test_event(self, events, expected):
        self.assertEqual(self.parse_string(events), expected)
    
    def _test_event_fail(self, hitobjs):
        with self.assertRaises(Exception):
            self.parse_string(hitobjs)

    # --- Tests ---
    def test_event(self):
        test_cases = {
            'normal': '0,0,12.jpg,0,0',
            'whitespace in type': ' 0 ,0,12.jpg,0,0',
            'comments': '//Background and Video events\n0,0,12.jpg,0,0\n//Hello',
            'blank line': '\n0,0,12.jpg,0,0\n\n',
            'whitespace line': '\t\n0,0,12.jpg,0,0\n       ',
        }
        EXPECTED = [osufile.EventBackground(type='0', time=0, filename='12.jpg', xoffset=0, yoffset=0)]

        test_case_crash = {}    # todo: test failure cases

        for name,data in test_cases.items():
            with self.subTest(case=name):
                self._test_event(data, EXPECTED)
        
        for name,data in test_case_crash.items():
            with self.subTest(case=name):
                self._test_event_fail(data)
    
    def test_unknown(self):
        self._test_event('a', [osufile.EventUnknown(type='a', params=[])])

    def test_background(self):
        test_cases = {
            'normal': '0,0,12.jpg,0,0',
            'quoted background': '0,0,"12.jpg",0,0',
            'extra arguments': '0,0,12.jpg,0,0,extra_argument',
            'missing yoffset': '0,0,12.jpg,0',
            'missing xoffset': '0,0,12.jpg',
        }
        EXPECTED = [osufile.EventBackground(type='0', time=0, filename='12.jpg', xoffset=0, yoffset=0)]

        test_case_crash = {
            'bad xoffset': '0,0,12.jpg,bad,0',
            'bad yoffset': '0,0,12.jpg,0,bad',
            'no background': '0,0',
        }

        for name,data in test_cases.items():
            with self.subTest(case=name):
                self._test_event(data, EXPECTED)
                self.roundtrip(data)
        
        for name,data in test_case_crash.items():
            with self.subTest(case=name):
                self._test_event_fail(data)