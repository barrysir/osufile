import unittest 
import osufile
from io import StringIO
from inspect import cleandoc

class NumbersSection(osufile.Section):
    def parse(self, section_name, lines):
        return [int(x) for x in lines]

    def write(self, file, section_name, data):
        for x in data:
            file.write(str(x) + '\n')

class MyParser(osufile.Parser):
    def __init__(self):
        super().__init__()
        self.sections['Numbers'] = NumbersSection()

class CustomSectionsTest(unittest.TestCase):
    def setUp(self):
        self.parser_with_numbers = MyParser()

    def test_roundtrip(self):
        inp = StringIO(SAMPLE_FILE)
        first_pass = osufile.parse(inp, parser=self.parser_with_numbers)
        out = StringIO()
        osufile.write(out, first_pass, parser=self.parser_with_numbers)
        out.seek(0)
        second_pass = osufile.parse(out, parser=self.parser_with_numbers)
        self.assertEqual(first_pass, second_pass)

SAMPLE_FILE = '''
osu file format v14

[General]
AudioFilename: audio.mp3
AudioLeadIn: 0
PreviewTime: 57420
Countdown: 1
SampleSet: Soft
StackLeniency: 0.7
Mode: 0
LetterboxInBreaks: 0
WidescreenStoryboard: 0

[Numbers]
3
-5
60
-128
'''