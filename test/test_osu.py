import unittest 
import osufile
from io import StringIO
from pathlib import Path
from inspect import cleandoc

__CWD__ = Path(__file__).parent.absolute()

# invalid tags like "Creator" are treated as if they weren't there

class OsuFileTest(unittest.TestCase):
    def parse_string(self, s):
        return osufile.parse(StringIO(s))
    
    def test_invalid_metadata_lines(self):
        sample = cleandoc('''
        osu file format v14

        [General]
        AudioFilename: audio.mp3
        badtag
        ''')
        osu = self.parse_string(sample)
        self.assertEqual(osu['General'], {'AudioFilename': 'audio.mp3'})