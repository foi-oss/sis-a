MEM   = 256*[16*'0']

REGS  = 8*[0]
PC    = 0
SP    = 0

STACK = []

FLAGS         = 0
FLG_NONE      = 0x00
FLG_ZERO      = 0x01
FLG_CARRY     = 0x02
FLG_SIGN      = 0x04
FLG_OVERFLOW  = 0x08
FLG_PARITY    = 0x10