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

#-------------------------------
#   Hit objects
#-------------------------------
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
    curvetype : str
    curvepoints : list
    slides : int
    length : float
    edgesounds : list
    edgesets : list
    sample: HitSample

@dataclass
class RawHitObject:
    x: int
    y: int
    time: int
    type: int
    sound: int
    others: list

#-------------------------------
#   Events
#-------------------------------
@dataclass
class EventUnknown:
    type : str
    params : list

@dataclass
class EventBackground:
    type : str
    time : int
    filename: str
    xoffset : int
    yoffset : int

@dataclass
class EventVideo:
    type : str
    time : int
    filename: str
    xoffset : int
    yoffset : int

@dataclass
class EventBreak:
    type : str
    time : int
    end : int