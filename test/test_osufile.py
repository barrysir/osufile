import unittest 
import osufile
from io import StringIO
from pathlib import Path
from inspect import cleandoc

__CWD__ = Path(__file__).parent.absolute()

class OsufileTest(unittest.TestCase):
    SAMPLE_FILE = __CWD__ / 'files' / 'cYsmix feat. Emmy - Tear Rain (jonathanlfj) [Insane].osu'
    SAMPLE_OUT = __CWD__ / 'out' / 'out.osu'

    def test_parse(self):
        as_path = self.SAMPLE_FILE
        as_str = str(as_path)

        with self.subTest('pathlib.Path'):
            osu_path = osufile.parse(as_path)
        with self.subTest('string filepath'):
            osu_str = osufile.parse(as_str)
        with self.subTest('file object'):
            with open(as_path, 'r', encoding='utf8') as as_fileobj:
                osu_fileobj = osufile.parse(as_fileobj)

        # check that they all parsed the same way
        self.assertEqual(osu_path, osu_str)
        self.assertEqual(osu_str, osu_fileobj)
    
    def test_write(self):
        def read_sample_file():
            with open(self.SAMPLE_OUT, 'r', encoding='utf8') as f:
                return f.read()
        
        # get some sample data to write out
        osu = osufile.parse(self.SAMPLE_FILE)
        
        as_path = self.SAMPLE_OUT
        as_str = str(as_path)

        with self.subTest('pathlib.Path'):
            osufile.write(as_path, osu)
            osu_path = read_sample_file()
        with self.subTest('string filepath'):
            osufile.write(as_str, osu)
            osu_str = read_sample_file()
        with self.subTest('file object'):
            as_fileobj = StringIO()
            osufile.write(as_fileobj, osu)
            osu_fileobj = as_fileobj.getvalue()
        
        # check that they all output the same way
        self.assertEqual(osu_path, osu_str)
        self.assertEqual(osu_str, osu_fileobj)
