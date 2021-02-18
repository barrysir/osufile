import osufile
from pathlib import Path

__CWD__ = Path(__file__).parent.absolute()

FILE_CACHE = {}

def get_osu(name):
    """
    Get an OsuFile object by name. (For now names are just filenames of test files.)
    Objects are lazily generated and cached afterwards.
    """
    # for now, name is the name of the file
    if name not in FILE_CACHE:
        FILE_CACHE[name] = osufile.parse(__CWD__ / 'files' / name)
    return FILE_CACHE[name]