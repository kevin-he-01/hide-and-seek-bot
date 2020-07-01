#! /usr/bin/env python3
# Allow a human to operate a bot (seeker or hider) using socket connection
# For server protocol, see `control-server-protocol.md`

import socket, curses, sys, pickle

from kit import Direction as Dir, Agent, Unit, Team

# Configs

port = 9009
sizeofsize = 4 # 32-bit
endianness = 'little'

poll_delay: float = 1 / 30
maploc = (5, 0) # Curses coordinate (y, x) to display a map

# 0:black, 1:red, 2:green, 3:yellow, 4:blue, 5:magenta, 6:cyan, and 7:white
seeker_color = 6
hider_color = 1
wall_color = 3

# botdir = Dir.STILL
keytodir = {'q': Dir.NORTHWEST, 'w': Dir.NORTH, 'e': Dir.NORTHEAST, 'd': Dir.EAST, 'c': Dir.SOUTHEAST, 'x': Dir.SOUTH,
    'z': Dir.SOUTHWEST, 'a': Dir.WEST, 's': Dir.STILL}

def recvall(sock, mlen):
    buffer = []
    while len(buffer) < mlen:
        bys = sock.recv(mlen - len(buffer))
        if len(bys) == 0:
            raise RuntimeError('Broken connection: expect {} bytes, only got {} bytes'.format(mlen, len(buffer)))
        buffer.extend(bys)
    return bytes(buffer)

def objrecv(sock):
    length = int.from_bytes(recvall(sock, sizeofsize), endianness)
    return pickle.loads(recvall(sock, length))

def procinst(c, inst, wlog, win):
    wlog('Received instruction from client: {}'.format(hex(inst)))
    if inst == 0x0:
        # sdata = bytes([botdir.value])
        unit: Unit = objrecv(c)
        assert isinstance(unit, Unit)
        agent: Agent = objrecv(c)
        assert isinstance(agent, Agent)
        win.erase()
        # win.addstr(0, 0, 'Input your direction: ')
        win.addstr(0, 0, '{} ID {}> '.format(agent.team.name, unit.id), curses.color_pair(seeker_color if agent.team == Team.SEEKER else hider_color))
        win.addstr(2, 0, 'Round: {}/200'.format(agent.round_num + 1))
        win.addstr(3, 0, 'Location (y, x): {}'.format((unit.y, unit.x)))
        draw_map(win, agent.map)
        win.refresh()
        while True:
            key = win.getkey()
            prockey(key)
            try:
                sdata = bytes([keytodir[key].value])
            except KeyError:
                win.addstr(1, 0, 'Invalid input', curses.color_pair(1))
                win.refresh()
            else:
                if c.send(sdata) == 0:
                    wlog('Client closes stream. Assuming that the competition has ended and exiting...')
                    sys.exit(3)
                break
        redraw(win)
    elif inst == 0xff:
        wlog('Client requested exit')
        sys.exit()
    else:
        raise RuntimeError("Illegal/unsupported request instruction: {}".format(hex(inst)))

def draw_map(win, mp): # TODO account for visibility and mark invisible blocks as dimmed 0/1
    for my in range(len(mp)):
        for mx in range(len(mp[my])):
            cell = mp[my][mx]
            if cell == 0:
                attr = 0
            elif cell == 1:
                attr = curses.color_pair(wall_color)
            elif cell % 2: # Hider
                attr = curses.color_pair(hider_color)
            else:
                attr = curses.color_pair(seeker_color)
            win.addch(maploc[0] + my, maploc[1] + mx * 2, curses.ACS_BLOCK if cell == 1 else (ord('0') + cell), attr)

def redraw(win):
    win.erase()
    win.addstr(0, 0, 'Waiting for my turn...', curses.A_DIM)
    win.refresh()

def prockey(key):
    if key == 'l':
        sys.exit()

def keypoll(win): # Poll ONCE, do nothing if there's no input
    try:
        key = win.getkey()
    except curses.error:
        pass
    else:
        prockey(key)

def init_color(): # Call this right after initscr
    curses.start_color()
    curses.use_default_colors() # VSCode light mode friendly
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(6, curses.COLOR_CYAN, -1)

def main(stdscr: curses.initscr):
    init_color()
    curses.cbreak()
    curses.noecho()
    curses.curs_set(0)
    # stdscr.nodelay(True) # Nonblocking
    redraw(stdscr)
    with open('control-server.log', 'w') as log:
        def wlog(s):
            log.write(s + '\n')
            log.flush()
        # create an INET, STREAMing socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
            # bind the socket to our private port on localhost
            serversocket.bind(('localhost', port))
            # become a server socket (Allow 2 clients, the hider and the seeker)
            serversocket.listen(1)
            wlog('Server started successfully')

            while True:
                wlog('Accepting new connections...')
                serversocket.settimeout(poll_delay) # Curses: nonblocking mode, server: timeout mode 
                stdscr.nodelay(True)
                while True:
                    keypoll(stdscr)
                    try:
                        c, _ = serversocket.accept()
                    except socket.timeout:
                        pass
                    else:
                        break
                stdscr.nodelay(False)
                c.settimeout(None) # Clear timeout
                wlog('Got a connection from the client.')
                with c:
                    while True:
                        data = c.recv(1)
                        if len(data) == 0:
                            wlog('Client closes connection. No more instructions from this client.')
                            break
                        procinst(c, data[0], wlog, stdscr)

if __name__ == "__main__":
    curses.wrapper(main)