# Valid client requests
- 1 byte (unless for special ones that append extra data, if any, which will be noted below)
- Types:
    - `0x0`: Get bot direction
        - Server response: one byte representing enum number for a direction in `kit.Direction`
    - `0x1`: Notify hitting walls/impassible objects
    - `0x2`-`0xfe`: Reserved
    - `0xff`: Shut down the server (but not the graphics panel), internal use only