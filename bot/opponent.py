from enum import Enum
# from kit import Agent, Team
import kit
from typing import Dict

class Opponent:
    def __init__(self, ourteam, oid: int, initx, inity):
        self.agent = ourteam
        self.map = ourteam.map
        self.id = oid
        self.initx = initx
        self.inity = inity

opponents: Dict[int, Opponent] = dict()

class OpponentSeeker(Opponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class OpponentHider(Opponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class Orientation(Enum):
    INDETERMINATE = 0
    HORIZONTAL = 1 # Horizontal symmetry, or mp[y][xdim - 1 - x] == mp[y][x] for all (x, y)
    VERTICAL = 2 # Vertical symmetry, or mp[ydim - 1 - y][x] == mp[y][x] for all (x, y)

def determine_map_orientation(mp, xdim, ydim):
    for y in range(ydim):
        for x in range(xdim):
            if (mp[y][x] == 1) != (mp[y][xdim - 1 - x] == 1): # Cannot be horizontal, so must be vertical
                return Orientation.VERTICAL
            if (mp[ydim - 1 - y][x] == 1) != (mp[y][x] == 1):
                return Orientation.HORIZONTAL
    return Orientation.INDETERMINATE

def init_opponents(ourteam):
    # global orientation
    orientation = determine_map_orientation(ourteam.map, ourteam.xdim, ourteam.ydim)
    for unit in ourteam.units:
        if orientation == Orientation.VERTICAL:
            opx = unit.x
            opy = ourteam.ydim - 1 - unit.y
        elif orientation == Orientation.HORIZONTAL:
            opx = ourteam.xdim - 1 - unit.x
            opy = unit.y
        else:
            opx = None
            opy = None
        oid = unit.id + 1 if ourteam.team == kit.Team.SEEKER else unit.id - 1
        op = OpponentHider(ourteam, oid, opx, opy) if ourteam.team == kit.Team.SEEKER else OpponentSeeker(ourteam, oid, opx, opy)
        opponents[oid] = op