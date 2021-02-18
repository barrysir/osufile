'''
Utils for handling the [Colours] section
'''

from ..combinator import ParserPair
from collections import OrderedDict

class ColourInterpreter:
    'Interprets the data found in the [Colours] section of an .osu file'
    class DefaultBase:
        osu_int = ParserPair(int, str)
    
    def __init__(self, base=DefaultBase):
        '''
        base: 
            object containing parsing functions
            contains one attribute:
            - osu_int: a ParserPair for parsing the combo colour int, e.g. the '4' in 'Combo4'
        '''
        self.base = base
        self.MAX_COMBO_COLOUR = 8
    
    def combo_ordering(self, colour_data):
        '''
        Returns the names of the attributes which make up the combo colours in order.
        ex. ['Combo1', 'Combo2', 'Combo3']
        '''
        combos = {}
        for c,v in colour_data.items():
            if c.startswith('Combo'):
                key = c[len('Combo'):]
                try:                                        # ignore any non-integer keys
                    key = self.base.osu_int.parse(key)
                except:
                    continue
                if not(0 < key <= self.MAX_COMBO_COLOUR):   # ignore any out of range keys
                    continue
                combos[key] = c
        return [combos[k] for k in sorted(combos.keys())]
    
    def group_combo(self, colour_data):
        '''
        Parses combo colours out of some colour data.
        Returns [combo colour tuples as a list], {remaining attributes}.
        Remaining attributes retain their original relative order.
        '''
        # have to be careful to preserve attribute ordering
        def remove_keys(keys, maindict):
            return OrderedDict((k,v) for k,v in colour_data.items() if k not in keys)
        
        # partition off the combo colours
        ordering = self.combo_ordering(colour_data)
        combo_colours = [colour_data[k] for k in ordering]
        others = remove_keys(ordering, colour_data)
        return combo_colours, others

    def join_combo(self, colours_and_others):
        '''
        Writes combo colours back into colour data.
        Takes a tuple of ([combo colour tuples as a list], {attributes}) and writes the colours back into the attributes.
        Returns the merged attributes.
        Attributes retain their ordering in the output.
        '''
        # have to be careful to preserve ordering
        # Combos placed first, then other keys after
        colours,others = colours_and_others
        out = OrderedDict()
        out.update((f'Combo{self.base.osu_int.write(i+1)}', v) for i,v in enumerate(colours))
        out.update(others)
        return out
    
    def parse(self, colour_data):
        'Parse all important data out of raw colour data, currently only parses combo'
        combo_colours,others = self.group_combo(colour_data)
        return combo_colours,others
    
    def write(self, colours_and_others):
        'Inverse function of parse()'
        colour_data = self.join_combo(colours_and_others)
        return colour_data

# --- convenience functions ---
_DEFAULT_PARSER = ColourInterpreter()
def combo_ordering(colour_data, parser=_DEFAULT_PARSER):
    '''
    Returns the names of the attributes which make up the combo colours in order.
    ex. ['Combo1', 'Combo2', 'Combo3']
    '''
    return parser.combo_ordering(colour_data)

def group_combo(colour_data, parser=_DEFAULT_PARSER):
    '''
    Parses combo colours out of some colour data.
    Returns [combo colour tuples as a list], {remaining attributes}.
    Remaining attributes retain their original relative order.
    '''
    return parser.group_combo(colour_data)

def join_combo(colours_and_others, parser=_DEFAULT_PARSER):
    '''
    Writes combo colours back into colour data.
    Takes a tuple of ([combo colour tuples as a list], {attributes}) and writes the colours back into the attributes.
    Returns the merged attributes.
    Attributes retain their ordering in the output.
    '''
    return parser.join_combo(colours_and_others)