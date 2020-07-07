import sys, queue, math
from enum import Enum
import vision, opponent as mod_op

from typing import List, Tuple, Dict, Union

# Constants
MOVE_DELTAS = [[0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1], [1, 0], [1, 1]]
## Should be indexed by the ordinal of Direction enum
## In (x, y) form
direction_deltas = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, 0)]
direction_move_deltas = direction_deltas[:8]
orthogonal_deltas = [(1, 0), (0, -1), (-1, 0), (0, 1)]
vision_range_sq = 48 # Squared vision range

loop_min_length = 6 # TODO 8 is safer and require less bot intelligence (stay still tactic when the enemy is directly at the other end of the loop)
# loop_length = ((du + 2) / 2 + (dv + 2) / 2) * 2 = du + dv + 4

def apply_direction(x, y, dir):
    newx = x
    newy = y
    if (dir == 0):
        newy -= 1
    elif (dir == 1):
        newy -= 1
        newx += 1
    elif (dir == 2):
        newx += 1
    elif (dir ==3):
        newx += 1
        newy += 1
    elif (dir == 4):
        newy += 1
    elif (dir == 5):
        newy += 1
        newx -= 1
    elif (dir == 6):
        newx -= 1
    elif (dir == 7):
        newx -= 1
        newy -= 1
    elif (dir == 8):
        pass
    
    return (newx, newy)

def read_input():
    """
    Reads input from stdin
    """
    try:
        return input()
    except EOFError as eof:
        raise SystemExit(eof)
      
class Team(Enum):
    SEEKER = 2
    HIDER = 3

class Direction(Enum):
    NORTH = 0
    NORTHEAST = 1
    EAST = 2
    SOUTHEAST = 3
    SOUTH = 4
    SOUTHWEST = 5
    WEST = 6
    NORTHWEST = 7
    STILL = 8

class UnitInfo:
    def __init__(self):
        self.hider_state = HiderState.FRESH
        self.hider_loop: Union[None, Loop] = None
        self.hiding_target = None

class Unit:
    def __init__(self, id, x, y, dist, agent):
        self.id = id
        self.x = x
        self.y = y
        self.distance = dist
        self.agent = agent
        # self.hider_state = HiderState.FRESH
        # self.hider_loop = None
        # self.hiding_target = None
    
    def get_info(self) -> UnitInfo:
        return self.agent.unit_infos[self.id]

    def move(self, dir: int) -> str:
        return "%d_%d" % (self.id, dir)

class NoPath(Exception):
    pass

class ObstructedLoop(Exception):
    pass

class Loop:
    def __init__(self, agent, x0, x1, y0, y1, u0, u1, v0, v1, loop_length):
        self.cell_set = set()
        self.loop_length = loop_length
        # for u in range(u0, u1 + 1):
        #     for v in range(v0, v1 + 1):
        def checkuv(u, v):
            return u0 - 1 <= u <= u1 + 1 and v0 - 1 <= v <= v1 + 1
        def checkall(x, y):
            u = x + y
            v = y - x
            return x0 - 1 <= x <= x1 + 1 and y0 - 1 <= y <= y1 + 1 and checkuv(u, v)
        # for u in range(u0 - 1, u1 + 2):
        #     for v in range(v0 - 1, v1 + 2):
        #         if (u + v) % 2 == 0:
        #             lix = (u - v) // 2
        #             liy = (u + v) // 2
        for lix in range(x0 - 1, x1 + 2):
            for liy in range(y0 - 1, y1 + 2):
                u = lix + liy
                v = liy - lix
                if checkuv(u, v):
                    good = False
                    for dx, dy in orthogonal_deltas:
                        if not checkall(lix + dx, liy + dy):
                            good = True
                            break
                    if good:
                        if not agent.walkable(lix, liy):
                            agent.vlog('Obstructed loop {} to {} at {}'.format((x0, y0), (x1, y1), (lix, liy)))
                            raise ObstructedLoop
                        self.cell_set.add((lix, liy))
                        # agent.loop_index[liy][lix].append(self) # Do it in agent after checking no ObstructedLoop
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1

class HiderState(Enum):
    HIDING = 0
    CIRCLING = 1
    FRESH = 2

class Agent:
    round_num = 0
    """
    Constructor for a new agent
    User should edit this according to their `Design`
    """
    def __init__(self):
        pass

    """
    Initialize Agent for the `Match`
    User should edit this according to their `Design`
    """
    def initialize(self): # Logging function
        meta = read_input().split(",")
        self.id = int(meta[0])
        self.team = Team(int(meta[1]))

        self._store_unit_info()
        

        [width, height] = [int(i) for i in (read_input().split(","))]
        self.map = []
        for _ in range(height):
            line = read_input().split(",")
            parsedList = []
            for j in range(len(line)):
                if line[j] != '':
                    parsedList.append(int(line[j]))

            self.map.append(parsedList)

        self.round_num = 0

        self._update_map_with_ids()
        ## Custom additions:
        self.walls = []
        self.ydim = len(self.map)
        self.xdim = len(self.map[0])
        for y, row in enumerate(self.map):
            for x, cell in enumerate(row):
                if cell == 1:
                    self.walls.append((x, y))
        # Initialize opponents
        mod_op.init_opponents(self)
        # # For hiders, find loops
        # if self.team == Team.HIDER:
        #     self.find_loops()
        self.unit_infos: Dict[int, UnitInfo] = dict()
        for unit in self.units:
            self.unit_infos[unit.id] = UnitInfo()
    
    def init_log(self, log, enable_log):
        """`log` must be a callable function"""
        self.log = log # Can only use log after the competition started (log initialized, in the main function)
        self.enable_log = enable_log # Avoid computationally expensive actions (Ex. constructing graphical representation of a map) needded only for logging
    
    def post_log_init(self):
        # For hiders, find loops
        if self.team == Team.HIDER:
            self.find_loops()
            # possible_locations = []
            # for y in range(self.ydim):
            #     for x in range(self.xdim):
            #         for op in mod_op.opponents.values():
            #             if op.possibility_map[y][x]:
            #                 possible_locations.append((x, y))
            # self.seeker_map = self.generate_distance_map(possible_locations)
    
    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = self.__dict__.copy()
        # Unpicklable
        del state['log']
        # Unnecessary
        del state['enable_log']
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.log = lambda *args, **kwargs: None
        self.enable_log = False
    
    def vlog(self, *args, **kwargs):
        self.log(*args, **kwargs, level='DEBUG')

    def _reset_map(self):

        for _, unit in enumerate(self.units):
            self.map[unit.y][unit.x] = 0

        for _, unit in enumerate(self.opposingUnits):
            self.map[unit.y][unit.x] = 0

    def _update_map_with_ids(self):

         # add unit ids to map
        for _, unit in enumerate(self.units):
            self.map[unit.y][unit.x] = unit.id
        
        # add unit ids to map
        for _, unit in enumerate(self.opposingUnits):
            self.map[unit.y][unit.x] = unit.id

    def _store_unit_info(self):
        units_and_coords = read_input().split(",")

        self.units = []
        for _, val in enumerate(units_and_coords):
            if (val != ""):
                [id, x, y, dist] = [int(k) for k in val.split("_")]
                self.units.append(Unit(id, x, y, dist, self))

        units_and_coords = read_input().split(",")
        
        self.opposingUnits = []
        for _, value in enumerate(units_and_coords):
            if (value != ""):
                [id, x, y] = [int(k) for k in value.split("_")]
                self.opposingUnits.append(Unit(id, x, y, -1, self))

    """
    Updates Agent's own known state of `Match`
    User should edit this according to their `Design
    """
    def update(self):
        self.round_num += 1
        self._reset_map()
        self._store_unit_info()
        self._update_map_with_ids()

    """
    End a turn
    """
    def end_turn(self):
        print('D_FINISH', flush=True)
        
    ## Additional functions

    def in_map(self, x, y):
        return 0 <= x < self.xdim and 0 <= y < self.ydim
    
    def walkable(self, x, y):
        return self.in_map(x, y) and self.map[y][x] != 1
    
    # def immediate_walkable(self, x, y):
    #     """Like `walkable` but accounts for other potentially mobile units"""
    #     return self.in_map(x, y) and self.map[y][x] == 0

    def sightNotBlocked(self, x1, y1, x2, y2):
        visited = set()
        def visit(x, y):
            if (x, y) not in visited:
                if x == x2 and y == y2:
                    return True
                visited.add((x, y)) 
                if self.walkable(x, y) and vision.checkBlocked(x1, y1, x2, y2, x, y):
                    for dx, dy in MOVE_DELTAS:
                        nx = x + dx
                        ny = y + dy
                        if vision.distance_squared(nx, ny, x2, y2) <= vision.distance_squared(x, y, x2, y2):
                            if visit(nx, ny):
                                return True
            return False
        return visit(x1, y1)
    
    def cellVisible(self, fromx: int, fromy: int, tox: int, toy: int):
        if vision.distance_squared(tox, toy, fromx, fromy) > vision_range_sq:
            return False
        return self.sightNotBlocked(tox, toy, fromx, fromy)
    
    def visibleCells(self, fromx, fromy):
        """Return an iterator of visible cells `(x1, y1), (x2, y2), ...` from (fromx, fromy)"""
        for toy in range(self.ydim):
            for tox in range(self.xdim):
                if self.cellVisible(fromx, fromy, tox, toy):
                    yield (tox, toy)
    
    # def anyVisibleCells(self, fromlist):
    #     """Return an iterator of visible cells `(x1, y1), (x2, y2), ...` from any member of `fromlist`: a list of "from" cells """
    #     for toy in range(self.ydim):
    #         for tox in range(self.xdim):
    #             for fromx, fromy in fromlist:
    #                 if self.cellVisible(fromx, fromy, tox, toy):
    #                     yield (tox, toy)
    #                     break
    
    def pathing(self, x1, y1, x2, y2, escape=False) -> Tuple[List[int], int]:
        # """
        # Return pair `(next_directions: list[int], distance)`
        # where `next_directions` is a list of ordinals of possible next `Direction`s.
        # Note: next direction is the step that should be taken by a unit at `(x1, y1)` or `None` when there's no path between the points.
        # For hiders, `None` means they are perfectly safe, while for seekers, it means the targeted hider is unreachable from them
        # Setting `escape` to `True` does inverse pathing that allow one to escape from a target rather than chasing one
        # """
        """
        Return pair `(next_directions: list[int], distance)`
        where `next_directions` is a list of ordinals of possible next `Direction`s.
        Note: next direction is the step that should be taken by a unit at `(x1, y1)` or raise `NoPath` when there's no path between the points.
        Note: if `escape` == True, not throwing `NoPath` doesn't necessarily mean there will be a good next move.
        If the hider is cornered but have a valid path to a seeker (for any direction it may move without hitting a wall brings it closer to the seeker),
        it will return an empty list.
        For hiders, `NoPath` means they are perfectly safe, while for seekers, it means the targeted hider is unreachable from them.
        """
        # assert self.walkable(x2, y2)
        bq = queue.Queue()
        bq.put((x2, y2, 8, 0)) # (x, y, inverse direction ordinal, distance from (x2, y2)/number of steps required)
        visited = set()
        distance = -1
        nxdirs: List[int] = []
        try:
            while True:
                x, y, dirnum, dist = bq.get_nowait()
                if self.walkable(x, y):
                    if x == x1 and y == y1:
                        if distance == -1:
                            distance = dist
                        elif dist > distance:
                            break
                        nxdirs.append(dirnum)
                        # return dirnum, dist
                    if distance == -1:
                        if (x, y) not in visited:
                            visited.add((x, y))
                            for ndirnum, (dx, dy) in enumerate(direction_move_deltas):
                                nx = x - dx # Direction is inversed since it searches path from (x2, y2) to (x1, y1)
                                ny = y - dy
                                # if self.walkable(nx, ny):
                                bq.put((nx, ny, ndirnum, dist + 1))
        except queue.Empty:
            pass
        if distance == -1:
            # return None
            raise NoPath
        else:
            if escape:
                nxsteps: List[int] = []
                # for ndirnum in nxdirs:
                for ndirnum, (dx, dy) in enumerate(direction_move_deltas):
                    if ndirnum not in nxdirs:
                        if self.walkable(x1 + dx, y1 + dy):
                            nxsteps.append(ndirnum)
            else:
                nxsteps = nxdirs
            return nxsteps, distance # TODO check other units when computing nxdirs using immediate_walkable?
    
    def opponents_update(self):
        opponents = mod_op.opponents
        dead_op_ids = []
        for op in opponents.values():
            # try:
            #     op.update() # Must be called before everything else that uses `opponents`
            # except Death:
            #     dead_op_ids.append(op.id)
            op.update()
        for unit in self.units:
            possible_op_ids = set()
            for y in range(self.ydim):
                for x in range(self.xdim):
                    if vision.distance_squared(x, y, unit.x, unit.y) == unit.distance:
                        for op in opponents.values():
                            if op.possibility_map[y][x]:
                                possible_op_ids.add(op.id)
            if not possible_op_ids:
                self.log('No opposing units could be at distance {} away as reported by game server'.format(unit.distance), unitid=unit.id, level='ERROR')
            elif len(possible_op_ids) == 1:
                opid = possible_op_ids.pop()
                self.log('Limited opponent {} to ring of distance {}'.format(opid, unit.distance), level='DEBUG')
                opponents[opid].limit(lambda x0, y0: vision.distance_squared(x0, y0, unit.x, unit.y) == unit.distance)
        for op in opponents.values():
            try:
                op.post_update()
            except mod_op.Death:
                if self.team == Team.HIDER:
                    self.log('Opposing seekers should never be dead!', level='ERROR')
                dead_op_ids.append(op.id)
        if dead_op_ids:
            self.log('Dead opponents in this round: {}. Removing them form the game.'.format(dead_op_ids))
        for dead_op_id in dead_op_ids:
            del opponents[dead_op_id]
        if self.enable_log:
            mod_op.trace_possibility_map(self)
        # Hider specific
        if self.team == Team.HIDER:
            possible_locations = []
            for y in range(self.ydim):
                for x in range(self.xdim):
                    for op in mod_op.opponents.values():
                        if op.possibility_map[y][x]:
                            possible_locations.append((x, y))
                            break
            self.seeker_map = self.generate_distance_map(possible_locations)
    
    def get_wall_block_dim(self, x0, y0, scanned): # Return none when connected to border
        # u = x + y, v = y - x
        minx = math.inf
        maxx = -math.inf
        miny = math.inf
        maxy = -math.inf
        minu = math.inf
        maxu = -math.inf
        minv = math.inf
        maxv = -math.inf
        # visited = set()
        bad = False
        def visit(x, y):
            nonlocal minx, maxx, miny, maxy, minu, maxu, minv, maxv, bad
            if not self.in_map(x, y):
                # return False
                bad = True # Continue scanning out neighbors
            elif self.map[y][x] == 1: # Non-walls not interested
                if not scanned[y][x]:
                    scanned[y][x] = True
                    u = x + y
                    v = y - x
                    minx = min(minx, x)
                    maxx = max(maxx, x)
                    miny = min(miny, y)
                    maxy = max(maxy, y)
                    minu = min(minu, u)
                    maxu = max(maxu, u)
                    minv = min(minv, v)
                    maxv = max(maxv, v)
                    for dx, dy in orthogonal_deltas:
                        nx = x + dx
                        ny = y + dy
                        visit(nx, ny)
            #             if not visit(nx, ny):
            #                 return False
            # return True
        visit(x0, y0)
        return None if bad else (minx, maxx, miny, maxy, minu, maxu, minv, maxv)
    
    # def slice_corners(self, x0, y0, x1, y1):
    #     for 

    def find_loops(self):
        """Find the convex hulls around "island" wall blocks (blocks of walls not attached to borders) within the map"""
        self.loop_index: List[List[List[Loop]]] = [[ [] for _ in range(self.xdim)] for _ in range(self.ydim)]
        self.loops = []
        scanned = [[False] * self.xdim for _ in range(self.ydim)]
        for y in range(self.ydim):
            for x in range(self.xdim):
                if self.map[y][x] == 1:
                    if not scanned[y][x]:
                        dims = self.get_wall_block_dim(x, y, scanned)
                        if dims != None:
                            x0, x1, y0, y1, u0, u1, v0, v1 = dims
                            loop_length = u1 - u0 + v1 - v0 + 4
                            self.vlog('Identified wall block from {} to {} and from (u, v) {} to {}. Loop length: {}'.format((x0, y0), (x1, y1), (u0, v0), (u1, v1), loop_length))
                            if loop_length >= loop_min_length:
                                try:
                                    loop = Loop(self, x0, x1, y0, y1, u0, u1, v0, v1, loop_length)
                                except ObstructedLoop:
                                    pass
                                else:
                                    self.loops.append(loop)
                                    for x, y in loop.cell_set:
                                        self.loop_index[y][x].append(loop)
                            # loop_length = u1 - u0 + v1 - v0 + 4
                            # self.vlog('Identified wall block from {} to {} and from (u, v) {} to {}. Loop length: {}'.format((x0, y0), (x1, y1), (u0, v0), (u1, v1), loop_length))
                            # # for u in range(u0, u1 + 1):
                            # #     for v in range(v0, v1 + 1):
                            # if loop_length >= loop_min_length:
                            #     for u in range(u0 - 1, u1 + 2):
                            #         for v in range(v0 - 1, v1 + 2):
                            #             if (u + v) % 2 == 0:
                            #                 lix = (u - v) // 2
                            #                 liy = (u + v) // 2
                            #                 if self.walkable(lix, liy):
                            #                     self.loop_index[liy][lix] += 1
        if self.enable_log:
            def genrows():
                def getcode(x, y):
                    count = len(self.loop_index[y][x])
                    if self.map[y][x] == 1:
                        assert count == 0
                        return 'W'
                    else:
                        sdigit = str(count)
                        if len(sdigit) == 1:
                            return sdigit
                        else:
                            return 'X'
                for y in range(self.ydim):
                    yield ' '.join((getcode(x, y) for x in range(self.xdim)))
            self.log('Loop index map:\n' + '\n'.join(genrows()))

    def debug_distance_map(self, mp):
        self.vlog('Distance map:\n' + '\n'.join([' '.join([str(e).ljust(4) for e in row]) for row in mp]))
    
    def generate_distance_map(self, targets):
        dist_map = [[math.inf] * self.xdim for _ in range(self.ydim)]
        bq = queue.Queue()
        for x0, y0 in targets:
            bq.put((x0, y0, 0)) # (x, y, inverse direction ordinal, distance from (x2, y2)/number of steps required)
        visited = set()
        try:
            while True:
                x, y, dist = bq.get_nowait()
                if self.walkable(x, y):
                    # if x == x1 and y == y1:
                    #     if distance == -1:
                    #         distance = dist
                    #     elif dist > distance:
                    #         break
                    #     nxdirs.append(dirnum)
                    if (x, y) not in visited:
                        visited.add((x, y))
                        dist_map[y][x] = dist
                        for (dx, dy) in direction_move_deltas:
                            nx = x + dx # Direction is inversed since it searches path from (x2, y2) to (x1, y1)
                            ny = y + dy
                            # if self.walkable(nx, ny):
                            bq.put((nx, ny, dist + 1))
        except queue.Empty:
            pass
        return dist_map