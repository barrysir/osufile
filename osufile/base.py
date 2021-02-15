from .parser import Parser
from .datatypes import OsuFile
import pathlib

def parse(file_or_fileobj, parser=Parser()):
    if isinstance(file_or_fileobj, str):
        with open(file_or_fileobj, 'r', encoding='utf8') as f:
            return parse(f, parser)
    elif isinstance(file_or_fileobj, pathlib.Path):
        with open(file_or_fileobj, 'r', encoding='utf8') as f:
            return parse(f, parser)
    else:
        return parser._parse(file_or_fileobj)
    
def write(file_or_fileobj, osu: OsuFile, parser=Parser()):
    if isinstance(file_or_fileobj, str):
        with open(file_or_fileobj, 'w', encoding='utf8') as f:
            return write(f, osu, parser)
    elif isinstance(file_or_fileobj, pathlib.Path):
        with open(file_or_fileobj, 'w', encoding='utf8') as f:
            return write(f, osu, parser)
    else:
        return parser._write(file_or_fileobj, osu)