from __future__ import print_function
import sys

import regs
import util
from debug import log

INSTRUCTIONS = map(lambda x: None, range(0, 32))
MNEM_DICT = {}

class instruction(object):
  def __init__(self, opcode, *args):
    self.opcode = opcode
    self.args_bit_size = args

  def __call__(self, fn):
    name = fn.__name__.replace('_', '')
    log(" # %5s %s" % (bin(self.opcode)[2:].zfill(5), name))

    def wrapper(r):
      args = map(util.binstr2int, util.partition(r, self.args_bit_size))
      log(" > %s@%d | %s" % (name, regs.PC, ' '.join(map(str, args))))
      return fn(*args)

    wrapper.__name__ = name
    wrapper.__bas__  = self.args_bit_size
    wrapper.__raw__  = fn

    if self.opcode in MNEM_DICT.values():
      print("Trying to assign opcode %d to '%s', but already assigned to '%s'." % (self.opcode,
        name,
        INSTRUCTIONS[self.opcode].__name__))
      exit(1)

    INSTRUCTIONS[self.opcode] = wrapper
    MNEM_DICT[name] = self.opcode

    return wrapper

def exec_instr(opcode, r):
  return INSTRUCTIONS[opcode](r)

### SPECIAL ###
@instruction(0b0)
def nop(*args):
  pass

### MATHS ###
@instruction(0b00001, 3, 3, 3)
def add(rd, r1, r2):
  regs.FLAGS = regs.FLG_NONE
  regs.REGS[rd] = regs.REGS[r1] + regs.REGS[r2]  
  
  if regs.REGS[rd] < 0:
    regs.FLAGS = regs.FLAGS | regs.FLG_SIGN
  if regs.REGS[rd] == 0:
    regs.FLAGS = regs.FLAGS | regs.FLG_ZERO
  if regs.REGS[rd] & 0x01FF:
    regs.FLAGS = regs.FLAGS | regs.FLG_CARRY
  if regs.REGS[rd] > 0x01FF:
    regs.FLAGS = regs.FLAGS | regs.FLG_OVERFLOW	

@instruction(0b00010, 3, 3, 3)
def sub(rd, r1, r2):
  regs.FLAGS = regs.FLG_NONE
  regs.REGS[rd] = regs.REGS[r1] - regs.REGS[r2]
  
  if regs.REGS[rd] < 0:
    regs.FLAGS = regs.FLAGS | regs.FLG_SIGN
  if regs.REGS[rd] == 0:
    regs.FLAGS = regs.FLAGS | regs.FLG_ZERO
  if regs.REGS[rd] & 0x01FF:
    regs.FLAGS = regs.FLAGS | regs.FLG_CARRY
  if regs.REGS[rd] > 0x01FF:
    regs.FLAGS = regs.FLAGS | regs.FLG_OVERFLOW

@instruction(0b00011, 3, 3, 3)
def mul(rd, r1, r2):
  regs.FLAGS = regs.FLG_NONE
  regs.REGS[rd] = regs.REGS[r1] * regs.REGS[r2]
  
  if regs.REGS[rd] < 0:
    regs.FLAGS = regs.FLAGS | regs.FLG_SIGN
  if regs.REGS[rd] == 0:
    regs.FLAGS = regs.FLAGS | regs.FLG_ZERO
  if regs.REGS[rd] & 0x01FF:
    regs.FLAGS = regs.FLAGS | regs.FLG_CARRY
  if regs.REGS[rd] > 0x01FF:
    regs.FLAGS = regs.FLAGS | regs.FLG_OVERFLOW

@instruction(0b00100, 3, 3, 3)
def mod(rd, r1, r2):
  regs.FLAGS = regs.FLG_NONE
  regs.REGS[rd] = regs.REGS[r1] % regs.REGS[r2]
  
  if regs.REGS[rd] == 0:
    regs.FLAGS = regs.FLAGS | regs.FLG_ZERO
  if regs.REGS[rd] & 0x01FF:
    regs.FLAGS = regs.FLAGS | regs.FLG_CARRY
  if regs.REGS[rd] > 0x01FF:
    regs.FLAGS = regs.FLAGS | regs.FLG_OVERFLOW

### SPECIAL (pt2) ###
@instruction(0b00101, 3)
def jmp(rd):
  regs.FLAGS = regs.FLG_NONE
  log(' # JMP to ' + str(regs.REGS[rd]))
  regs.PC = regs.REGS[rd]

@instruction(0b00110, 8)
def call(rd):
  regs.FLAGS = regs.FLG_NONE
  log(" # pushing PC and FLAGS to stack ")
  regs.STACK.append(regs.PC)
  regs.STACK.append(regs.FLAGS)
  [push.__raw__(reg) for reg in range(0, 8)]
  log(" # jumping to %d" % rd)
  regs.PC = rd

@instruction(0b00111)
def ret():
  regs.FLAGS = regs.FLG_NONE
  log(" # restoring registers")
  [pop.__raw__(reg) for reg in range(7, -1, -1)]
  regs.FLAGS = regs.STACK.pop()
  regs.PC = regs.STACK.pop()
  
  log(" # PC=%d SP=%d FLAGS=%d" % (regs.PC, len(regs.STACK), regs.FLAGS))

@instruction(0b01000)
def halt():
  raise NotImplementedError()

#TODO add flags after this point
@instruction(0b01001, 3, 3, 3)
def _and(rd, rx, ry):
  regs.REGS[rd] = regs.REGS[rx] & regs.REGS[ry]

@instruction(0b01010, 3, 3, 3)
def _or(rd, rx, ry):
  regs.REGS[rd] = regs.REGS[rx] | regs.REGS[ry]

@instruction(0b01011, 3, 3, 3)
def nor(rd, rx, ry):
  regs.REGS[rd] = ~(regs.REGS[rx] | regs.REGS[ry])

@instruction(0b01100, 3, 3, 3)
def xor(rd, rx, ry):
  regs.REGS[rd] = regs.REGS[rx] ^ regs.REGS[ry]

@instruction(0b01101, 3, 3)
def _not(rd, rx):
  regs.REGS[rd] = ~regs.REGS[rx]

@instruction(0b01110, 3, 3, 3)
def shl(rd, rx, ry):
  regs.REGS[rd] = regs.REGS[rx] << regs.REGS[ry]

@instruction(0b01111, 3, 3, 3)
def shr(rd, rx, ry):
  regs.REGS[rd] = regs.REGS[rx] >> regs.REGS[ry]

### CONDITIONS AND BRANCHING ###
@instruction(0b10000, 3, 3, 3)
def seq(rd, rx, ry):
  regs.REGS[rd] = int(regs.REGS[rx] == regs.REGS[ry])

@instruction(0b10001, 3, 3, 3)
def slt(rd, rx, ry):
  regs.REGS[rd] = int(regs.REGS[rx] < regs.REGS[ry])

@instruction(0b10010, 3, 3, 3)
def sgt(rd, rx, ry):
  regs.REGS[rd] = int(regs.REGS[rx] > regs.REGS[ry])

@instruction(0b10011, 3, 3, 3)
def jeq(rd, rx, ry):
  raise NotImplementedError()

@instruction(0b10100, 3, 3, 3)
def jlt(rd, rx, ry):
  raise NotImplementedError()

@instruction(0b10101, 3, 3, 3)
def jgt(rd, rx, ry):
  raise NotImplementedError()

### STACKS ###
@instruction(0b10111, 3)
def gsr(rx):
  if rx & 0b100 != 0:
    regs.REGS[4] = regs.PC
  if rx & 0b010 != 0:
    regs.REGS[5] = len(regs.STACK) - 1
  if rx & 0b001 != 0:
    regs.REGS[6] = regs.FLAGS

@instruction(0b11000, 3)
def push(rx):
  raise NotImplementedError()

@instruction(0b11001, 3)
def pop(rd):
  log(" # popping '%d' off the stack" % regs.STACK[len(regs.STACK) - 1])
  regs.REGS[rd] = regs.STACK.pop()

@instruction(0b11010, 3)
def pull(rd):
  regs.REGS[rd] = regs.STACK[regs.STACK[len(regs.STACK) - 1]]

### MEMORY ###
@instruction(0b11011, 3, 8)
def store(rx, md):
  val = util.fixedbin(regs.REGS[rx], 16)
  log(" # store %s (%d) => m%s" % (val, regs.REGS[rx], md))
  regs.MEM[md] = val

@instruction(0b11100, 3, 8)
def load(rd, mx):
  regs.REGS[rd] = util.binstr2int(regs.MEM[mx])

@instruction(0b11101, 3, 8)
def loadv(rd, val):
  regs.REGS[rd] = val

@instruction(0b11110, 3, 3)
def mv(rx, rd):
  regs.REGS[rd] = regs.REGS[rx]

@instruction(0b11111, 3, 3)
def displ(rx, ry):
  for r in range(rx, ry+1):
    sys.stderr.write(chr(regs.REGS[r]))
