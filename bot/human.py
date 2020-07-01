from kit import Agent, Team, Direction, apply_direction, Unit

import socket, pickle

port = 9009
sizeofsize = 4 # 32-bit
endianness = 'little'

def sendobj(cs, obj):
    pobj = pickle.dumps(obj)
    cs.sendall(len(pobj).to_bytes(sizeofsize, endianness))
    cs.sendall(pobj)

def getdirectionvalue(unit, agent):
    if agent.round_num == 0:
        return Direction.STILL.value # Workaround a bug that lag updates if the first move is not done swiftly
    else:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cs:
            cs.connect(('localhost', port))
            cs.send(bytes([0x0]))
            sendobj(cs, unit)
            sendobj(cs, agent)
            # cs.sendall(bytes([0x0, agent.round_num, agent.id]))
            # return Direction(cs.recv(1)[0])
            return cs.recv(1)[0]

def init(agent: Agent):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cs:
        cs.connect(('localhost', port))
        cs.send(bytes([0x2]))
        sendobj(cs, agent)

def handle(agent: Agent, commands: list):
    for _, unit in enumerate(agent.units):
        game_map = agent.map # the map
        # unit.id is id of the unit
        # unit.x unit.y are its coordinates, unit.distance is distance away from nearest opponent
        # game_map is the 2D map of what you can see. 
        # game_map[i][j] returns whats on that tile, 0 = empty, 1 = wall, 
        # anything else is then the id of a unit which can be yours or the opponents

        # get direction from a human controller
        myDirection = getdirectionvalue(unit, agent)

        # apply direction to current unit's position to check if that new position is on the game map
        (x, y) = apply_direction(unit.x, unit.y, myDirection)
        if (x < 0 or y < 0 or x >= len(game_map[0]) or y >= len(game_map)):
            # we do nothing if the new position is not in the map
            # TODO notify human and request to display 'Hit the wall' on the server
            pass
        else:
            commands.append(unit.move(myDirection))

def notifyexit():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cs:
            cs.connect(('localhost', port))
            cs.send(bytes([0x3]))
    except ConnectionRefusedError:
        pass # ASSUMING the server crashed, so no action