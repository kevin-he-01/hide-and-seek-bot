# Valid client requests
- 1 byte (unless for special ones that append extra data, if any, which will be noted below)
- Types (depend on byte `0`):
    - `0x0`: Get bot direction
        - Client data bytes:
            <!-- - `1`: Round number (under 200 rounds limit)
            - `2`: Agent type
            - `3`: Unit ID
            - `4`: Unit X coord
            - `5`: Unit Y coord -->
            - A `Unit` object encoded in `OBJ`
            - The `Agent` `OBJ` corresponding to the `Unit`
        - `OBJ` format, byte locations are relative to the start of this stream of bytes
            - `0-3`: Data length (32 bit little endian unsigned integer)
            - `4-?`: The pickled Python object
        - Server response: one byte representing enum number for a direction in `kit.Direction`
    - `0x1`: Notify hitting walls/other units on the same team
    - `0x2`: Do initialization: send an _initialized_ agent object before the 1st round
        <!-- - Help initializing `vision` module
        - Notify server of map dimension, walls location, team side etc. -->
        - Should only be done once
        - Is this necessary? maybe do this in `0x0`
    - `0x3`: Notify end of the game, or that the client have exited
    - `0xff`: Shutdown the server (including the graphic panel), reserved
## Notes
- The client shall not hang or delay response when there's a connection to the server (since it will block the ncurses interface)
    - that applies **even** between instructions, by sending multiple instructions without closing connection, the client must respond swiftly
    - to perform computationally expensive steps, the client must first close the connection so the server may keep its interface responsive
- Due to the `0x2` instruction, the same server **may not** be reused for multiples rounds or be used for _both_ seekers and hiders, doing so results in undefined behavior