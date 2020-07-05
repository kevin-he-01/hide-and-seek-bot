import sys
import queue
from enum import Enum
import vision, opponent

# Constants
MOVE_DELTAS = [[0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1], [1, 0], [1, 1]]
## Should be indexed by the ordinal of Direction enum
## In (x, y) form
direction_deltas = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, 0)]
direction_move_deltas = direction_deltas[:8]
vision_range_sq = 48 # Squared vision range

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

class Unit:
    def __init__(self, id, x, y, dist):
        self.id = id
        self.x = x
        self.y = y
        self.distance = dist

    def move(self, dir: int) -> str:
        return "%d_%d" % (self.id, dir)

class NoPath(Exception):
    pass

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
    def initialize(self):
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
        opponent.init_opponents(self)

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
                self.units.append(Unit(id, x, y, dist))

        units_and_coords = read_input().split(",")
        
        self.opposingUnits = []
        for _, value in enumerate(units_and_coords):
            if (value != ""):
                [id, x, y] = [int(k) for k in value.split("_")]
                self.opposingUnits.append(Unit(id, x, y, -1))

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
    
    def pathing(self, x1, y1, x2, y2, escape=False):
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
        nxdirs = []
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
                nxsteps = []
                # for ndirnum in nxdirs:
                for ndirnum, (dx, dy) in enumerate(direction_move_deltas):
                    if ndirnum not in nxdirs:
                        if self.walkable(x1 + dx, y1 + dy):
                            nxsteps.append(ndirnum)
            else:
                nxsteps = nxdirs
            return nxsteps, distance # TODO check other units when computing nxdirs using immediate_walkable?