import math

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
    divisorA = ((y4-y3)*(x2-x1) - (x4-x3)*(y2-y1))
    divisorB = ((y4-y3)*(x2-x1) - (x4-x3)*(y2-y1))
    if divisorA == 0 or divisorB == 0:
        return False
    uA = ((x4-x3)*(y1-y3) - (y4-y3)*(x1-x3)) / divisorA
    uB = ((x2-x1)*(y1-y3) - (y2-y1)*(x1-x3)) / divisorB
    # uA = jsdiv( ((x4-x3)*(y1-y3) - (y4-y3)*(x1-x3)) , ((y4-y3)*(x2-x1) - (x4-x3)*(y2-y1)) )
    # uB = jsdiv( ((x2-x1)*(y1-y3) - (y2-y1)*(x1-x3)) , ((y4-y3)*(x2-x1) - (x4-x3)*(y2-y1)) )
    if 0 <= uA <= 1 and 0 <= uB <= 1:
        return True
    return False

def checkBlocked(x1: int, y1: int, x2: int, y2: int, rx: int, ry: int):
    """Checks if line from the center of cell `x1, y1` to that of cell `x2, y2` passes through unit cell with lowest x & lowest y corner at `x3, y3`"""
    return lineIntersectsCell(x1 + 0.5, y1 + 0.5, x2 + 0.5, y2 + 0.5, float(rx), float(ry))

def distance_squared(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return dx * dx + dy * dy
