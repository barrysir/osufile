import unittest 
import osufile
from io import StringIO
from pathlib import Path
from inspect import cleandoc
from .SectionTest import SectionTest

from osufile.combinator import ParserPair

class MetadataSectionTest(SectionTest):
    def setUp(self):
        # create sample lookup table
        pint = ParserPair(int, str)
        pfloat = ParserPair(float, str)
        pstr = ParserPair(str, str)
        table = {
            'AudioFilename': pstr,
            'PreviewTime': pint,
            'SampleSet': pstr,
            'StackLeniency': pfloat,
            'TimelineZoom': pfloat,
        }

        base = osufile.Parser()
        parser = osufile.sections.Metadata(base, table)
        super().setUp('MetadataTesting', parser)
    
    def test_empty_section(self):
        self._test_section('', {})
        self._test_section('\n\n', {})
    
    def test_unknown_tags(self):
        # unknown tags should parse as strings
        self._test_section('NotATag:false', {'NotATag': 'false'})
    
    def test_stripping(self):
        self._test_section('  AudioFilename : \t audio.mp3  ', {'AudioFilename': 'audio.mp3'})
    
    def test_multiple_definitions(self):
        self._test_section('AudioFilename: audio.mp3\nAudioFilename: audio2.mp3', {'AudioFilename': 'audio2.mp3'})
    
    def test_ignore_non_tags(self):
        sample = cleandoc('''
        AudioFilename: audio.mp3

        badtag
        o0o0o0o0o    
        ''')
        self._test_section(sample, {'AudioFilename': 'audio.mp3'})
    
    def test_preserves_order(self):
        # To check for order it does a raw string comparison which isn't great... 
        # can't figure out how to get the order without either implementing a parser yourself
        # or by reading the ordering from the built dict which isn't trustworthy
        # because the parser can shuffle around the keys while building the dict
        # I can't think of a better way to check for this
        sample = cleandoc('''
        TimelineZoom:3.0
        AudioFilename:audio.mp3
        PreviewTime:195852
        StackLeniency:0.5
        ''')
        sample += '\n'  # cleandoc() strips whitespace, manually add a trailing newline
        osu = self.parse_string(sample)
        s = self.write_string(osu)
        self.assertEqual(sample, s)
    
    def test_invalid_data_in_tag(self):
        # PreviewTime is an int but gets passed something that can't be parsed, should throw
        self._test_section_fail('AudioFilename: audio.mp3\nPreviewTime: asdf')
    
    def test_roundtrip(self):
        sample = cleandoc('''
        TimelineZoom: 3
        AudioFilename:audio.mp3
        PreviewTime:195852
        StackLeniency:0.5
        AudioFilename: audio.mp3
        NewTag: hello
        ''')
        self._test_roundtrip(sample)
    