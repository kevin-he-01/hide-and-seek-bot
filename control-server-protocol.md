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
            - `1-4`: Data length (32 bit little endian)
            - `5-?`: A pickled `Agent` object
        - Server response: one byte representing enum number for a direction in `kit.Direction`
    - `0x1`: Notify hitting walls/other units on the same team
    - `0x2`: Do initialization: notify server of map dimension, walls location, etc.
        - Do only once for all bots, keep track of whether this is sent on the first run
        - Is this necessary? maybe do this in `0x0`
    - `0x3`: Notify end of the game
    - `0xff`: Shutdown the server (including the graphic panel), reserved