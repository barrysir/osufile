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

@dataclass 
class HitSample:
    normal_set: int
    addition_set: int
    index: int
    volume: int
    filename: str

@dataclass
class HitCircle:
    x: int
    y: int
    time: int
    type: int
    sound: int
    sample: HitSample

@dataclass
class Hold:
    x: int
    y: int
    time: int
    type: int
    sound: int
    endtime: int
    sample: HitSample

@dataclass
class Spinner:
    x: int
    y: int
    time: int
    type: int
    sound: int
    endtime: int
    sample: HitSample

@dataclass
class Slider:
    x: int
    y: int
    time: int
    type: int
    sound: int
    curveType : str
    curvePoints : list
    slides : int
    length : float
    edgeSounds : list
    edgeSets : list
    sample: HitSample

@dataclass
class RawHitObject:
    x: int
    y: int
    time: int
    type: int
    sound: int
    others: list