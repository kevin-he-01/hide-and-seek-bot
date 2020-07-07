from enum import Enum
import kit, vision
from typing import Dict
# from typing import TYPE_CHECKING
# if TYPE_CHECKING: # Not available on 3.5.1 (only on 3.5.2 not worth the risk)
#     from kit import Agent, Team

class Death(Exception): # An opponent should is expected to be tagged
    pass

class Opponent:
    def __init__(self, ourteam, oid: int, initx, inity):
    # def __init__(self, ourteam: 'Agent', oid: int, initx, inity):
        self.agent = ourteam
        self.map = ourteam.map
        self.id = oid
        # noinit = initx == None
        # indexed by [y][x]
        if initx == None:
            self.possibility_map = [[ourteam.map[y][x] != 1 for x in range(ourteam.xdim)] for y in range(ourteam.ydim)]
            # self._clear_primary_loc()
            self.primary_loc = None
            self.lastseen = None
            self.location_count = ourteam.ydim * ourteam.xdim
            # FIXME self.possible_list here
        else:
            self.possibility_map = [[False] * ourteam.xdim for _ in range(ourteam.ydim)] # True = possible location, False = impossible location (including walls)
            self.set_primary_loc(initx, inity)
            # self.force_lastseen = True
    
    # def get_primary_loc(self):
    #     if self.primary_loc != None:
    #         return self.primary_loc
    #     elif self.force_lastseen:
    #         return self.lastseen
    #     else:
    #         return None
    
    def _set_primary_loc(self, x, y): # Force set without setting possibility map correspondingly
        self.primary_loc = (x, y)
        self.lastseen = (x, y)

    def set_primary_loc(self, x, y):
        assert self.agent.walkable(x, y), 'Trying to set primary location in a wall or outside boundary: {}'.format((x, y))
        for y0 in range(self.agent.ydim):
            for x0 in range(self.agent.xdim):
                self.possibility_map[y0][x0] = (x0 == x and y0 == y)
        self._set_primary_loc(x, y)
        self.location_count = 1
        self.possible_list = [(x, y)]
    
    def _clear_primary_loc(self): # Note: it forces values to be None without altering `self.possibility_map` or statistics (Ex. `self.location_count` at all)
        self.primary_loc = None
    
    def update_stat(self):
        """Updates location possibility counter (`location_count`), primary locations, and other stats"""
        cnt = 0
        locy = -1
        locx = -1
        self.possible_list = []
        for y0 in range(self.agent.ydim):
            for x0 in range(self.agent.xdim):
                if self.possibility_map[y0][x0]:
                    locx = x0
                    locy = y0
                    cnt += 1
                    self.possible_list.append((x0, y0))
                else:
                    if self.lastseen != None and self.lastseen[0] == x0 and self.lastseen[1] == y0:
                        self.lastseen = None # Last seen is not actually what its literal meaning suggests. It is the most plausible location if the hider never moves
                        # which is usually the case for dumb bots that doesn't move away from its initial determinable location.
        self.location_count = cnt
        if cnt == 1:
            self._set_primary_loc(locx, locy)
        elif cnt == 0:
            raise Death
        else:
            self._clear_primary_loc()
    
    def expand_possibility_map(self):
        deep_copy_map = [row[:] for row in self.possibility_map]
        for y0 in range(self.agent.ydim):
            for x0 in range(self.agent.xdim):
                if deep_copy_map[y0][x0]:
                    for dx, dy in kit.direction_move_deltas:
                        nx = x0 + dx
                        ny = y0 + dy
                        if self.agent.walkable(nx, ny):
                            self.possibility_map[ny][nx] = True

    # def visualize_possibility_map(self):
    #     """Iterator returning rows of graphical representation of possibility map"""
    #     def getcode(x, y):
    #         if self.possibility_map[y][x]:
    #             if self.agent.map[y][x] == 1:
    #                 # Should NOT happen!
    #                 return 'E'
    #             elif self.primary_loc == (x, y):
    #                 return 'P'
    #             elif self.lastseen == (x, y):
    #                 return 'L'
    #             else:
    #                 return 'p'
    #         else:
    #             if self.agent.map[y][x] == 1:
    #                 return 'W'
    #             else:
    #                 return str(self.agent.map[y][x])
    #     for y in range(self.agent.ydim):
    #         yield ' '.join([getcode(x, y) for x in range(self.agent.xdim)])
    
    def vlog(self, *args, **kwargs):
        # self.agent.log(*args, **kwargs, level='DEBUG')
        self.agent.vlog(*args, **kwargs)
    
    def trace(self):
        self.vlog('Opponent {} location info:'.format(self.id))
        self.vlog('Primary location: {}'.format(self.primary_loc))
        self.vlog('Last seen location: {}'.format(self.lastseen))
        self.vlog('Location possibility count: {}'.format(self.location_count))
        # self.vlog('Full possibility map:\n' + '\n'.join(self.visualize_possibility_map()))
    
    def limit(self, predicate):
        """Predicate may access `self.possibility_map[y0][x0]` to get the current value
        BUT must never read any other cell (Ex. self.possibility_map[y0+1][x0+1]).
        Doing such is undefined behavior
        """
        for y0 in range(self.agent.ydim):
            for x0 in range(self.agent.xdim):
                self.possibility_map[y0][x0] &= bool(predicate(x0, y0))
    
    def update(self):
        if self.agent.round_num > 0:
            self.expand_possibility_map()
        ourteam = self.agent
        for op_unit in ourteam.opposingUnits:
            if op_unit.id == self.id:
                self.set_primary_loc(op_unit.x, op_unit.y) # The opponent is in some unit's visible area
                break
        else:
            # fromlist = [(our_unit.x, our_unit.y) for our_unit in ourteam.units]
            # for vx, vy in ourteam.anyVisibleCells(fromlist):
            #     self.possibility_map[vy][vx] = False # Not possible since the visible area has no units
            for toy in range(ourteam.ydim):
                for tox in range(ourteam.xdim):
                    for our_unit in ourteam.units:
                        if vision.distance_squared(our_unit.x, our_unit.y, tox, toy) < our_unit.distance or ourteam.cellVisible(our_unit.x, our_unit.y, tox, toy):
                            self.possibility_map[toy][tox] = False
        #     self.update_stat()
        # if self.agent.enable_log:
        #     self.trace()
    
    def post_update(self):
        """Must be called whenever self.possibility_map is updated
        Ex. by `update` or `limit`
        Raise `Death` when it is expected to not exist in the game anymore (tagged)"""
        self.update_stat()
        if self.agent.enable_log:
            self.trace()

opponents: Dict[int, Opponent] = dict()

def map_key(agent, ids):
    # Opponent key
    agent.vlog('Key: r={0}; Y={0},{1}; g={1}; C={1},{2}; b={2}; P={0},{2}; A={0},{1},{2}'.format(*ids))

def trace_possibility_map(agent):
    agent.vlog('Full possibility map:\n' + '\n'.join(visualize_possibility_map(agent)))

def visualize_possibility_map(agent):
    ids = [5, 7, 9] if agent.team == kit.Team.SEEKER else [4, 6, 8]
    map_key(agent, ids)
    i1, i2, i3 = ids
    idstokey = {(i1,): 'r', (i1, i2): 'Y', (i2,): 'g', (i2, i3): 'C', (i3,): 'b', (i1, i3): 'P', (i1, i2, i3): 'A'}
    def getcode(x, y):
        opids = []
        for op in opponents.values():
            if op.possibility_map[y][x]:
                if agent.map[y][x] == 1:
                    # Should NOT happen!
                    return 'E'
                # elif op.primary_loc == (x, y):
                #     return 'P'
                # elif op.lastseen == (x, y):
                #     return 'L'
                else:
                    # return 'p'
                    opids.append(op.id)
            # else:
        if opids:
            return idstokey[tuple(opids)]
        else:
            if agent.map[y][x] == 1:
                return 'W'
            else:
                return str(agent.map[y][x])
    for y in range(agent.ydim):
        yield ' '.join([getcode(x, y) for x in range(agent.xdim)])

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
        # op = OpponentHider(ourteam, oid, opx, opy) if ourteam.team == kit.Team.SEEKER else OpponentSeeker(ourteam, oid, opx, opy)
        op = Opponent(ourteam, oid, opx, opy) if ourteam.team == kit.Team.SEEKER else Opponent(ourteam, oid, opx, opy)
        opponents[oid] = op