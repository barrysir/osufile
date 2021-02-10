import unittest 
import osufile
from io import StringIO
from pathlib import Path
from inspect import cleandoc

class SectionTest(unittest.TestCase):
    def setUp(self, section_name, parser):
        super().setUp()
        self.section_name = section_name
        self.parser = parser

    def parse_string(self, text):
        '''Run some section text through the parser and return the output'''
        return self.parser.parse(self.section_name, text.split('\n'))
    
    def write_string(self, parsed_section):
        '''Pass data into writer and return output as a string'''
        s = StringIO()
        self.parser.write(s, self.section_name, parsed_section)
        return s.getvalue()

    # Helper tests
    def _test_section(self, text, expected):
        '''Assert that some section text parses to an expected output'''
        self.assertEqual(self.parse_string(text), expected)
    
    def _test_section_fail(self, text):
        '''Assert that some section text fails to parse'''
        with self.assertRaises(Exception):
            self.parse_string(text)
    
    def _test_roundtrip(self, section_data):
        '''Run a roundtrip test (parse -> write -> parse again -> check that first and second parse are the same)'''
        if isinstance(section_data, str):
            first_pass = self.parse_string(section_data)
        else:
            first_pass = section_data
        
        second_pass = self.parse_string(self.write_string(first_pass))
        self.assertEqual(first_pass, second_pass)
    