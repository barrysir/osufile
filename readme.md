# osufile

Modular hackable .osu parser. Supports reading and writing. Default implementation tries to match osu!'s parsing behaviour, but you can override parts of the parser to disable or add functionality.

## Requirements

 * Python 3.7 or later

## Example usage

```python
import osufile

osu = osufile.parse(r'cYsmix feat. Emmy - Tear Rain (jonathanlfj) [Insane].osu')
print(osu['General']['AudioFilename'])  # 'tearrain.mp3'
print(osu['Metadata']['Artist'])        # 'cYsmix feat. Emmy'
print(osu['TimingPoints'][0])           # TimingPoint(time=852, tick=468.75, ...)
print(osu['HitObjects'][-1])            # Spinner(x=256, y=192, time=239094, ...)

osu['Difficulty']['ApproachRate'] = 9.5
osu['Metadata']['Version'] += ' AR9.5'

osufile.write(r'cYsmix feat. Emmy - Tear Rain (jonathanlfj) [Insane AR9.5].osu', osu)
```

Creating and using custom parsers (design still WIP, subject to change):

```python
import osufile
from decimal import Decimal

class MyParser(osufile.Parser):
    def parse_float(self, x): return Decimal(x)
    def write_float(self, x): return str(x)

parser = MyParser()
osu = osufile.parse('infile.osu', parser=parser)
osufile.write('outfile.osu', osu, parser=parser)
```

```python
import osufile

class NumbersSection(osufile.Section):
    def parse(self, section_name, lines):
        return [int(x) for x in lines]

    def write(self, file, section_name, data):
        for x in data:
            file.write(str(x) + '\n')

class ParserWithNumbers(osufile.Parser):
    def __init__(self):
        super().__init__()
        self.sections['Numbers'] = NumbersSection()

parser_with_numbers = ParserWithNumbers()
osu = osufile.parse('infile_with_numbers.osu', parser=parser_with_numbers)
osufile.write('outfile_with_numbers.osu', osu, parser=parser_with_numbers)
```

## Running tests

`python -m unittest -v test.[file within test/ folder]`

e.g. `python -m unittest -v test.test_osu`