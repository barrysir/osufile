import unittest 
import osufile
from io import StringIO
from pathlib import Path
from inspect import cleandoc
from .SectionTest import SectionTest

from osufile.combinator import ParserPair

# extra attributes: ignored
# repeated attributes: last one is used
# whitespace: is not stripped! (prefix is not stripped, suffix is)
# newlines: ignored
# no value: crashes
# physical ordering doesn't matter
# numbers can go "1,2,3,6"
# Combo(not a number) with value: works
# Combo(not a number) with invalid value: crashes

# colour:
#   invalid value: crashes
#   extra values: ignored
#   missing values: crashes
#   whitespace stripped
#   floats: crashes
#   negative numbers: treated as 0
#   large numbers: treated as 0

class ColoursSectionTest(SectionTest):
    def setUp(self):
        base = osufile.Parser()
        parser = osufile.sections.Colours(base)
        super().setUp('Colours', parser)
    
    def test_empty_section(self):
        self._test_section('', {})
        self._test_section('\n\n', {})
    
    def test_unknown_colours(self):
        self._test_section(
            'Combo6 : 0,255,0\nNotAColour:255,255,255\nComboasdf : 0,0,0',
            {'Combo6': (0,255,0), 'NotAColour': (255,255,255), 'Comboasdf': (0,0,0)}
        )
    
    def test_blank_lines(self):
        self._test_section('Combo1 : 0,255,0\n\t\nCombo2 : 255,0,0\n    ', {'Combo1': (0,255,0), 'Combo2': (255,0,0)})

    def test_whitespace(self):
        # whitespace is stripped from the back but not the front
        self._test_section('Combo6   : 0,255,0\n\tCombo6: 0,255,0', {'Combo6': (0,255,0), '\tCombo6': (0,255,0)})

    def test_multiple_definitions(self):
        self._test_section('Combo1 : 224,51,1\nCombo1 : 255,255,255', {'Combo1': (255,255,255)})
    
    def test_no_value(self):
        self._test_section_fail('Combo1:')
        self._test_section_fail('Combo1')
    
    def test_colour_extra_arguments(self):
        self._test_section('Combo1 : 224,51,1,255', {'Combo1': (224,51,1)})
    
    def test_colour_missing_arguments(self):
        self._test_section_fail('Combo1 : 224,51')
    
    def test_colour_whitespace(self):
        self._test_section('Combo1 : 224  ,  51  ,1   ', {'Combo1': (224,51,1)})
    
    def test_preserves_order(self):
        # To check for order it does a raw string comparison which isn't great... 
        # can't figure out how to get the order without either implementing a parser yourself
        # or by reading the ordering from the built dict which isn't trustworthy
        # because the parser can shuffle around the keys while building the dict
        # I can't think of a better way to check for this
        sample = cleandoc('''
        Combo6 : 0,255,0
        Combo1 : 224,51,1
        Combo3 : 185,102,74
        ''')
        sample += '\n'  # cleandoc() strips whitespace, manually add a trailing newline
        osu = self.parse_string(sample)
        s = self.write_string(osu)
        self.assertEqual(sample, s)
    
    def test_roundtrip(self):
        sample = cleandoc('''
        Combo6 : 0,255,0
        Combo1 : 224, 51 ,1
        Combo3 : 185,102,74
        SliderTrackOverride: 0,1,2
        SliderBorder: 5,4,3
        ''')
        self._test_roundtrip(sample)
    