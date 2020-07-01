import math
from kit import Unit, Agent

vision_range_sq = 48 # Squared vision range

# def sign(n):
#     return math.copysign(1.0, n) > 0

def jsdiv(a, b): # Emulate javascript division (return NaN and infinity rather than throwing ZeroDivisionError)
    if b == 0:
        if a == 0 or a != a:
            return math.nan
        else:
            # return math.inf if sign(a) == sign(b) else -math.inf
            return math.copysign(math.inf, a / math.copysign(1.0, b))
    else:
        return a / b

# Adapted from https://github.com/acmucsd/hide-and-seek-ai/blob/f06770a423b0602df8a6393e0c470c2027bc54a5/src/Map/index.ts
def lineIntersectsCell(x1: float, y1: float, x2: float, y2: float, rx: float, ry: float):
    """Checks if line from `x1, y1` to `x2, y2` intersects unit cell with lowest x & lowest y corner at `x3, y3`"""
    rw = 1
    rh = 1
    left =   lineIntersectLine(x1,y1,x2,y2, rx,ry,rx, ry+rh)
    right =  lineIntersectLine(x1,y1,x2,y2, rx+rw,ry, rx+rw,ry+rh)
    top =    lineIntersectLine(x1,y1,x2,y2, rx,ry, rx+rw,ry)
    bottom = lineIntersectLine(x1,y1,x2,y2, rx,ry+rh, rx+rw,ry+rh)
    if left or right or top or bottom:
        return True
    return left or right or top or bottom

def lineIntersectLine(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, x4: float, y4: float):
    """Checks if line from `x1, y1` to `x2, y2` intersects line from `x3, y3` to `x4, y4`"""
    # uA = ((x4-x3)*(y1-y3) - (y4-y3)*(x1-x3)) / ((y4-y3)*(x2-x1) - (x4-x3)*(y2-y1))
    # uB = ((x2-x1)*(y1-y3) - (y2-y1)*(x1-x3)) / ((y4-y3)*(x2-x1) - (x4-x3)*(y2-y1))
    uA = jsdiv( ((x4-x3)*(y1-y3) - (y4-y3)*(x1-x3)) , ((y4-y3)*(x2-x1) - (x4-x3)*(y2-y1)) )
    uB = jsdiv( ((x2-x1)*(y1-y3) - (y2-y1)*(x1-x3)) , ((y4-y3)*(x2-x1) - (x4-x3)*(y2-y1)) )
    if uA >= 0 and uA <= 1 and uB >= 0 and uB <= 1:
        return True
    return False

def checkBlocked(x1: int, y1: int, x2: int, y2: int, rx: int, ry: int):
    return lineIntersectsCell(x1 + 0.5, y1 + 0.5, x2 + 0.5, y2 + 0.5, float(rx), float(ry))

def init(agent: Agent):
    """Must be called before some functions can be safely called"""
    global walls
    walls = []
    for y, row in enumerate(agent.map):
        for x, cell in enumerate(row):
            if cell == 1:
                walls.append((x, y))

def distance_squared(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return dx * dx + dy * dy

def isCellVisible(unit: Unit, x: int, y: int):
    if distance_squared(unit.x, unit.y, x, y) > vision_range_sq:
        return False
    for wx, wy in walls:
        if checkBlocked(unit.x, unit.y, x, y, wx, wy):
            return False
    return True