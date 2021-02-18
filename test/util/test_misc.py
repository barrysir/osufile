import unittest 
import osufile.util.misc as misc
from io import StringIO
from pathlib import Path
from inspect import cleandoc
from collections import OrderedDict
from ..testdata import get_osu

class DefaultFilenameUtilsTest(unittest.TestCase):
    def test_normal(self):
        osu = get_osu('cYsmix feat. Emmy - Tear Rain (jonathanlfj) [Insane].osu')
        self.assertEqual(
            misc.default_filename(osu),
            'cYsmix feat. Emmy - Tear Rain (jonathanlfj) [Insane].osu'
        )