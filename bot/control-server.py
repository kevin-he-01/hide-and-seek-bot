#! /usr/bin/env python3
# Allow a human to operate a bot (seeker or hider) using socket connection
# For server protocol, see `control-server-protocol.md`

import socket, curses, sys, pickle

from kit import Direction as Dir, Agent, Unit

# botdir = Dir.STILL
keytodir = {'q': Dir.NORTHWEST, 'w': Dir.NORTH, 'e': Dir.NORTHEAST, 'd': Dir.EAST, 'c': Dir.SOUTHEAST, 'x': Dir.SOUTH,
    'z': Dir.SOUTHWEST, 'a': Dir.WEST, 's': Dir.STILL}

port = 9009
sizeofsize = 4 # 32-bit
endianness = 'little'

# def server(log: open):
#     pass

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
        win.addstr(0, 0, '{} ID {}> '.format(agent.team.name, unit.id))
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

poll_delay: float = 1 / 30

def init_color(): # Call this right after initscr
    curses.start_color()
    curses.use_default_colors() # VSCode light mode friendly
    curses.init_pair(1, curses.COLOR_RED, -1) # Warning red color

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
            # become a server socket (Allow only one client)
            serversocket.listen(0)
            wlog('Server started successfully')

            while True:
                wlog('Accepting new connections...')
                c, _ = serversocket.accept()
                with c:
                    while True:
                        c.settimeout(poll_delay) # Curses: nonblocking mode, server: timeout mode 
                        stdscr.nodelay(True)
                        while True:
                            keypoll(stdscr)
                            try:
                                data = c.recv(1)
                            except socket.timeout:
                                pass
                            else:
                                break
                        stdscr.nodelay(False)
                        c.settimeout(None) # Clear timeout
                        if len(data) == 0:
                            wlog('Client closes connection. No more instructions from this client.')
                            break
                        procinst(c, data[0], wlog, stdscr)

if __name__ == "__main__":
    curses.wrapper(main)