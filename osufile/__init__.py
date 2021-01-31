from .parser import Parser

def parse(file_or_fileobj, parser=Parser()):
    if isinstance(file_or_fileobj, str):
        with open(file_or_fileobj, 'r', encoding='utf8') as f:
            return parse(f, parser)
    else:
        return parser.parse(file_or_fileobj)
    
def write(file_or_fileobj, parser=Parser()):
    if isinstance(file_or_fileobj, str):
        with open(file_or_fileobj, 'w', encoding='utf8') as f:
            return write(f, parser)
    else:
        return parser.write(file_or_fileobj)