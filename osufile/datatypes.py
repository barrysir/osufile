import collections
from dataclasses import dataclass

class OsuFile(collections.OrderedDict):
    header: str

@dataclass 
class TimingPoint:
    time: int
    tick: float 
    meter: int
    sampleset: int 
    sampleindex: int 
    volume: int 
    uninherited: bool
    effects: int

# @dataclass 
# class HitSample:
#     normal_set: int
#     addition_set: int
#     index: int
#     volume: int
#     filename: str

@dataclass
class HitCircle:
    x: int
    y: int
    time: int
    type: int
    sound: int
    sample: str # HitSample

@dataclass
class RawHitObject:
    x: int
    y: int
    time: int
    type: int
    sound: int
    others: list