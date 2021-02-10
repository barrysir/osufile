import unittest 
import osufile
from io import StringIO
from inspect import cleandoc
from decimal import Decimal

class MyParser(osufile.Parser):
    def parse_float(self, x): return Decimal(x)
    def write_float(self, x): return str(x)

class CustomParsersTest(unittest.TestCase):
    def setUp(self):
        self.my_parser = MyParser()

    def test_roundtrip(self):
        inp = StringIO(SAMPLE_FILE)
        first_pass = osufile.parse(inp, parser=self.my_parser)

        # check that floats were parsed into Decimal
        self.assertTrue(isinstance(first_pass['General']['StackLeniency'], Decimal))

        # round trip
        out = StringIO()
        osufile.write(out, first_pass, parser=self.my_parser)
        out.seek(0)
        second_pass = osufile.parse(out, parser=self.my_parser)
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
'''