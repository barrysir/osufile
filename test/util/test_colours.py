import unittest 
import osufile.util.colours as colours
from io import StringIO
from pathlib import Path
from inspect import cleandoc
from collections import OrderedDict

class ColourUtilsTest(unittest.TestCase):
    def test_combo_colours_empty(self):
        colour_data = OrderedDict()
        self.assertEqual(colours.combo_ordering(colour_data), [])
        self.assertEqual(colours.group_combo(colour_data), ([], colour_data))
    
    def test_combo_colours_normal(self):
        colour_data = OrderedDict([
            ('Combo1', (255, 0, 1)), 
            ('Combo2', (255, 0, 2)), 
            ('Combo3', (255, 0, 3)), 
            ('Combo4', (255, 0, 4)),
            ('SliderBorder', (1, 2, 3)),
        ])
        self.assertEqual(colours.combo_ordering(colour_data), ['Combo1', 'Combo2', 'Combo3', 'Combo4'])
        self.assertEqual(colours.group_combo(colour_data), (
            [(255, 0, 1), (255, 0, 2), (255, 0, 3), (255, 0, 4)], 
            OrderedDict([('SliderBorder', (1, 2, 3))])
        ))
    
    def test_combo_colours_out_of_order(self):
        colour_data = OrderedDict([
            ('Combo1', (255, 0, 1)), 
            ('Combo4', (255, 0, 4)), 
            ('Combo3', (255, 0, 3)), 
            ('SliderBorder', (1, 2, 3)),
            ('Combo2', (255, 0, 2)),
        ])
        self.assertEqual(colours.combo_ordering(colour_data), ['Combo1', 'Combo2', 'Combo3', 'Combo4'])
        self.assertEqual(colours.group_combo(colour_data), (
            [(255, 0, 1), (255, 0, 2), (255, 0, 3), (255, 0, 4)], 
            OrderedDict([('SliderBorder', (1, 2, 3))])
        ))
    
    def test_combo_colours_attributes_preserve_order(self):
        colour_data = OrderedDict([
            ('Combo1', (255, 0, 1)), 
            ('Combo2', (255, 0, 2)),
            ('Combo3', (255, 0, 3)),  
            ('Combo4', (255, 0, 4)),
            ('SliderTrackOverride', (50, 60, 70)),
            ('SliderBorder', (1, 2, 3)),
        ])
        self.assertEqual(colours.group_combo(colour_data), (
            [(255, 0, 1), (255, 0, 2), (255, 0, 3), (255, 0, 4)], 
            OrderedDict([('SliderTrackOverride', (50, 60, 70)), ('SliderBorder', (1, 2, 3))])
        ))
    
    def test_combo_colours_max_count(self):
        colour_data = OrderedDict([
            ('Combo1', (255, 0, 1)), 
            ('Combo2', (255, 0, 2)),
            ('Combo3', (255, 0, 3)),  
            ('Combo4', (255, 0, 4)),
            ('Combo5', (255, 0, 5)),
            ('Combo6', (255, 0, 6)),
            ('Combo7', (255, 0, 7)),
            ('Combo8', (255, 0, 8)),
            ('Combo9', (255, 0, 9)),
        ])

        expected = colour_data.copy()
        expected.pop('Combo9')
        self.assertEqual(colours.combo_ordering(colour_data), list(expected.keys()))
        self.assertEqual(colours.group_combo(colour_data)[0], list(expected.values()))
    
    def test_combo_colours_invalid(self):
        colour_data = OrderedDict([
            ('Combo-2', (255, 0, 3)),  
            ('Combo0', (255, 0, 0)),   
            ('Combo1', (255, 0, 1)),   
            ('Combo2.0', (255, 0, 1)), 
            ('Combo', (255, 0, 4)),
            ('Comboasdf', (255, 0, 2)),
        ])
        self.assertEqual(colours.combo_ordering(colour_data), ['Combo1'])
        self.assertEqual(colours.group_combo(colour_data)[0], [(255, 0, 1)])
    
    def test_combo_colours_roundtrip(self):
        colour_data = OrderedDict([
            ('Combo1', (255, 0, 1)), 
            ('Combo4', (255, 0, 4)), 
            ('SliderTrackOverride', (50, 60, 70)),
            ('Combo3', (255, 0, 3)), 
            ('SliderBorder', (1, 2, 3)),
            ('Combo2', (255, 0, 2)),
        ])

        first_pass = colours.group_combo(colour_data)
        second_pass = colours.group_combo(colours.join_combo(first_pass))
        self.assertEqual(first_pass, second_pass)
    
    def test_override_base(self):
        from osufile.combinator import ParserPair

        # mock int/str, contains a "triggered" variable which is set to True when the function is called
        triggered = None
        def reset():
            nonlocal triggered
            triggered = False
        def mock_int(s):
            nonlocal triggered
            triggered = True
            return int(s)
        def mock_str(s):
            nonlocal triggered
            triggered = True
            return str(s)

        # custom parser
        class CustomBase:
            osu_int = ParserPair(mock_int, mock_str)
        
        # context manager to check that the custom parsing functions were called
        class CheckTriggered:
            def __init__(self, parent):
                self.parent = parent        # use "parent" here because we need to refer to the parent's self
            def __enter__(self):
                reset()
            def __exit__(self, type, value, traceback):
                nonlocal triggered
                self.parent.assertTrue(triggered)
        
        colour_data = OrderedDict([
            ('Combo1', (255, 0, 1)), 
            ('Combo2', (255, 0, 2)), 
            ('Combo3', (255, 0, 3)), 
            ('Combo4', (255, 0, 4)),
            ('SliderBorder', (1, 2, 3)),
        ])

        # note the parser=myparser in each of these calls
        # it's pretty easy to miss... might be worth a redesign
        # or you could call functions on myparser directly
        myparser = colours.ColourInterpreter(base = CustomBase())
        check_triggered = CheckTriggered(self)
        with check_triggered:
            self.assertEqual(colours.combo_ordering(colour_data, parser=myparser), ['Combo1', 'Combo2', 'Combo3', 'Combo4'])

        with check_triggered:
            self.assertEqual(colours.group_combo(colour_data, parser=myparser), (
                [(255, 0, 1), (255, 0, 2), (255, 0, 3), (255, 0, 4)], 
                OrderedDict([('SliderBorder', (1, 2, 3))])
            ))

        with check_triggered:
            self.assertEqual(colours.join_combo((
                [(255, 0, 1), (255, 0, 2), (255, 0, 3), (255, 0, 4)], 
                OrderedDict([('SliderBorder', (1, 2, 3))])
            ), parser=myparser), colour_data)