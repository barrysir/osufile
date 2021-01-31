# osufile

Tiny easily hackable .osu parser. Supports reading and writing. Default implementation tries to match osu!'s parsing behaviour, but you can override parts of the parser to disable or add functionality.

## Requirements

 * Python 3.5 or later

## Running tests

`python -m unittest -v test.[file you want to test]`

e.g. `python -m unittest -v test.test_osu`