#! /usr/bin/env python3
# Allow a human to operate a bot (seeker or hider) using socket connection
# For server protocol, see `control-server-protocol.md`

import socket, curses, threading, sys

from kit import Direction as Dir

botdir = Dir.STILL
dirlock = threading.Lock()
keytodir = {'q': Dir.NORTHWEST, 'w': Dir.NORTH, 'e': Dir.NORTHEAST, 'd': Dir.EAST, 'c': Dir.SOUTHEAST, 'x': Dir.SOUTH,
    'z': Dir.SOUTHWEST, 'a': Dir.WEST, 's': Dir.STILL}

port = 9009

def server_thread():
    with open('control-server-log.txt', 'w') as log:
        server(log)

def server(log: open):
    # create an INET, STREAMing socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
        # bind the socket to our private port on localhost
        serversocket.bind(('localhost', port))
        # become a server socket
        serversocket.listen(5)

        while True:
            c, _ = serversocket.accept()
            requesteddir = False
            with c:
                data = c.recv(1)
                if len(data) == 0:
                    raise RuntimeError("Client unexpectedly ends the stream")
                inst = data[0]
                if inst == 0x0:
                    requesteddir = True
                    with dirlock:
                        sdata = bytes([botdir.value])
                    c.send(sdata)
                elif inst == 0xff:
                    return
                else:
                    raise RuntimeError("Illegal/unsupported request instruction: 0x{:x}".format(inst))
            if requesteddir:
                log.write('Client requested direction.\n')
                log.flush()

def redraw(win):
    win.move(0, 0)
    # win.clrtobot()
    win.clrtoeol()
    win.addstr('Current Direction: {}'.format(botdir)) # No need to lock since the server (other) thread can only read from (not write to) botdir
    win.refresh()

def main(stdscr: curses.initscr):
    server = threading.Thread(target=server_thread)
    try:
        server.start()
        def update_dir(dr):
            # TODO acquire thread lock before editing direction
            global botdir
            with dirlock:
                botdir = dr
            redraw(stdscr)
        curses.cbreak()
        curses.noecho()
        curses.curs_set(0)
        redraw(stdscr)

        while True:
            ch = stdscr.getch()
            if ch == ord('l'):
                break
            if ch < 128:
                try:
                    dr = keytodir[chr(ch)]
                except KeyError:
                    pass
                else:
                    update_dir(dr)
    finally:
        # Shut down the server when the graphic panel crashes/closes
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientsocket:
                clientsocket.connect(('localhost', port))
                clientsocket.send(bytes([0xff]))
        except ConnectionRefusedError: # OK if the server haven't started yet or crashed
            if server.is_alive():
                print('WARNING: Server connection refused yet server thread is still alive!', file=sys.stderr)
                print('Please manually shut down this server by killing this process if appropriate.', file=sys.stderr)

if __name__ == "__main__":
    curses.wrapper(main)