import unittest 
import osufile
from io import StringIO
from pathlib import Path
from inspect import cleandoc
from .SectionTest import SectionTest

class EventSectionTest(SectionTest):
    def setUp(self):
        base = osufile.Parser()
        parser = osufile.sections.Events(base)
        return super().setUp('Events', parser)
    
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
                self._test_section(data, EXPECTED)
        
        for name,data in test_case_crash.items():
            with self.subTest(case=name):
                self._test_section_fail(data)
    
    def test_unknown(self):
        self._test_section('a', [osufile.EventUnknown(type='a', params=[])])

    def test_background(self):
        test_cases = {
            'normal': '0,0,12.jpg,0,0',
            'quoted': '0,0,"12.jpg",0,0',
            'extra arguments': '0,0,12.jpg,0,0,extra_argument',
            'missing yoffset': '0,0,12.jpg,0',
            'missing xoffset': '0,0,12.jpg',
        }
        EXPECTED = [osufile.EventBackground(type='0', time=0, filename='12.jpg', xoffset=0, yoffset=0)]
        for name,data in test_cases.items():
            with self.subTest(case=name):
                self._test_section(data, EXPECTED)
                self._test_roundtrip(data)
            
        # spaces should not be stripped
        test_cases_spaces = {
            'spaces': ('  12.jpg  ', '  12.jpg  '),
            'spaces outside quotes': (' "12.jpg" ', ' "12.jpg" '),
            'spaces within quotes': ('"  12.jpg  "', '  12.jpg  '),     # quotes are stripped
        }
        for name,(input,output) in test_cases_spaces.items():
            with self.subTest(case=name):
                data = f'0,0,{input},0,0'
                EXPECTED2 = [osufile.EventBackground(type='0', time=0, filename=output, xoffset=0, yoffset=0)]
                self._test_section(data, EXPECTED2)
                self._test_roundtrip(data)

        test_case_crash = {
            'bad xoffset': '0,0,12.jpg,bad,0',
            'bad yoffset': '0,0,12.jpg,0,bad',
            'no filepath': '0,0',
        }
        for name,data in test_case_crash.items():
            with self.subTest(case=name):
                self._test_section_fail(data)

    def test_video(self):
        test_cases = {
            'normal': '1,0,video.mp4,0,0',
            'quoted': '1,0,"video.mp4",0,0',
            'extra arguments': '1,0,video.mp4,0,0,extra_argument',
            'missing yoffset': '1,0,video.mp4,0',
            'missing xoffset': '1,0,video.mp4',
        }
        EXPECTED = [osufile.EventVideo(type='1', time=0, filename='video.mp4', xoffset=0, yoffset=0)]
            
        for name,data in test_cases.items():
            with self.subTest(case=name):
                self._test_section(data, EXPECTED)
                self._test_roundtrip(data)
                
        with self.subTest(case='normal_video'):
            self._test_section('Video,0,video.mp4,0,0', [osufile.EventVideo(type='Video', time=0, filename='video.mp4', xoffset=0, yoffset=0)])

        # spaces should not be stripped
        test_cases_spaces = {
            'spaces': ('  12.jpg  ', '  12.jpg  '),
            'spaces outside quotes': (' "12.jpg" ', ' "12.jpg" '),
            'spaces within quotes': ('"  12.jpg  "', '  12.jpg  '),     # quotes are stripped
        }
        for name,(input,output) in test_cases_spaces.items():
            with self.subTest(case=name):
                data = f'1,0,{input},0,0'
                EXPECTED2 = [osufile.EventVideo(type='1', time=0, filename=output, xoffset=0, yoffset=0)]
                self._test_section(data, EXPECTED2)
                self._test_roundtrip(data)   
        
        test_case_crash = {
            'bad xoffset': '1,0,video.mp4,bad,0',
            'bad yoffset': '1,0,video.mp4,0,bad',
            'no filepath': '1,0',
        }
        for name,data in test_case_crash.items():
            with self.subTest(case=name):
                self._test_section_fail(data)

    def test_breaks(self):
        test_cases = {
            'normal': '2,0,1000',
            'extra arguments': '2,0,1000,extra_argument',
        }
        EXPECTED = [osufile.EventBreak(type='2', time=0, end=1000)]
        for name,data in test_cases.items():
            with self.subTest(case=name):
                self._test_section(data, EXPECTED)
                self._test_roundtrip(data)

        test_case_crash = {
            'missing arguments': '2,0',
            'bad starttime': '2,bad,1000',
            'bad endtime': '2,0,bad',
        }
        for name,data in test_case_crash.items():
            with self.subTest(case=name):
                self._test_section_fail(data)