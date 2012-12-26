from __future__ import print_function
from base64 import b64decode
import itertools

import debug, util, instructions

COMPILER_ERRORS = []
COMPILER_VARS   = {}
COMPILER_LABELS = {}
COMPILER_INSTRS = {}
LBL_COUNTER     = 0
ADDR_SHIFT      = 0

def compiler_instr(fn):
  COMPILER_INSTRS[fn.__name__] = fn
  return fn

def error(line, msg):
  COMPILER_ERRORS.append("%5d: %s" % (line, msg))

@compiler_instr
def var(source, name, val):
  debug.log(" # %d: %s = %s" % (source[0], name, val))
  COMPILER_VARS[name] = val

@compiler_instr
def begin(source, lbl):
  global LBL_COUNTER
  n = source[0]

  if not lbl in COMPILER_LABELS:
    debug.log(" # %d: registering new label '%s' with id %d" % (n, lbl, LBL_COUNTER))
    COMPILER_LABELS[lbl] = {'id': LBL_COUNTER, 'start': n, 'end': -1}
    LBL_COUNTER += 1
    return [(".%d" % (LBL_COUNTER - 1)).ljust(16, '.')]
  else:
    debug.log(" # %d: updating position of label '%s'" % (n, lbl))
    COMPILER_LABELS[lbl]['start'] = n
    debug.log(" # leaving a label mark")
    return [("." + str(COMPILER_LABELS[lbl]['id'])).ljust(16, '.')]

@compiler_instr
def end(source, lbl):
  if not lbl in COMPILER_LABELS:
    error(source[0], ".end called for an undefined label: " + lbl)
    return
  n = source[0]
  COMPILER_LABELS[lbl]['end'] = n

@compiler_instr
def endf(source, lbl):
  if not lbl in COMPILER_LABELS:
    error(source[0], ".endf called for an undefined label: " + lbl)
    return
  n = source[0]
  debug.log(" # %d: inserting implicit return instruction" % n)
  COMPILER_LABELS[lbl]['end'] = n
  return [util.fixedbin(instructions.MNEM_DICT['ret'], 5).ljust(16, '0')]

@compiler_instr
def log(source, *args):
  print(" # %d:" % source[0], *args)

@compiler_instr
def shift(source, count):
  global ADDR_SHIFT
  debug.log(" # Shifting all addresses by", count)
  ADDR_SHIFT = int(count)

def compile(f, fout):
  global ADDR_SHIFT
  parsed_source = None

  with open(f, 'r') as source:
    parsed_source = map(parse_line, enumerate(source.readlines()))

  for label in COMPILER_LABELS:
    info = COMPILER_LABELS[label]
    if info['end'] == -1:
      error(info['start'], "missing a matching .end call for label: " + label)

  if len(COMPILER_ERRORS) != 0:
    return (False, COMPILER_ERRORS)

  # 0. flatten the list
  parsed_source = list(itertools.chain(*parsed_source))

  # 1. remove blank lines
  pps = [line for line in parsed_source if len(line) != 0]

  # 2. find all label markers and calculate their absolute positions
  abspos = {}
  for (n, line) in enumerate(pps):
    if line[0] == '.':
      label_id = line.replace('.', '')
      abspos[label_id] = ADDR_SHIFT + (n - len(abspos.keys()))
      pps[n] = None
      debug.log(" # %d: found marker for label '%s'" % (n, label_id))

  pps = [line for line in pps if line != None]

  # 3. replace label markers with actual locations
  #    (and expand $! with current position)
  for (n, line) in enumerate(pps):
    pos = line.find('%')
  
    if pos != -1:
      label_id = line[pos:line.rfind('%')+1].replace('%', '')
      replacement = abspos[label_id]
      pps[n] = (line[0:pos] + util.fixedbin(replacement, 8)).ljust(16, '0')
      debug.log("%3d: inserting label address lbl%s -> %d" % (n, label_id, replacement))
  
    pos = line.find('!')
    if pos != -1:
      debug.log("%3d: inserting current location" % n)
      pps[n] = (line[0:pos] + util.fixedbin(n, 8)).ljust(16, '0')

    debug.log("%3d: %s" % (n, pps[n]))

  with open(fout, 'wb') as out:
    debug.log(" # Writing binary to '%s'..." % fout)
    [out.write(raw_instr(line)) for line in pps]

  if ADDR_SHIFT > 0:
    print(" Note: You're using address shifting. Binary won't be executable on its own.")

  return (True, None)

def raw_instr(instr):
  if len(instr) == 0:
    return ""
  return ('\\x' + '\\x'.join(util.chunks(instr, 2))).decode('string_escape')

def parse_line((n, line)):
  line = line.strip()
  if len(line) == 0 or line[0:2] == '--':
    return ''

  line = line.split('--', 1)[0].strip().split()
  instr = line[0]

  if instr[0] == '.':
    ret = exec_compiler_instr(n, instr[1:], line[1:])
    return [''] if ret == None else ret

  if instr[0] == '`':
    instr = instr.strip('`')
    debug.log(" # %d: found raw data '%s...'" % (n, instr[0:10]))
    raw_data = map(util.chr2binstr, b64decode(instr))
    data = []

    line = ""
    for byte in raw_data:
      if len(line) == 16:
        data.append(line)
        line = ""

      try:
        int('0b' + byte, 2)
        line += byte
      except ValueError, e:
        line += bin(int('0x' + byte, 16))[2:]

    debug.log(" # %d: expanded data takes up %d bytes" % (n, len(data)/2))
    return data

  try:
    opcode = instructions.MNEM_DICT[instr]
  except KeyError, e:
    error(n, "unknown instruction: '%s'" % instr)
    return ''

  bas = instructions.INSTRUCTIONS[opcode].__bas__
  parsed_args = [parse_arg(n, arg.strip()) for arg in line[1:]]
  try:
    args= [arg.zfill(bas[n]) for (n, arg) in enumerate(parsed_args)]
  except IndexError, e:
    error(n, "too many arguments: '%s' requires %d but provided with %d" % (
      instr,
      len(bas),
      len(parsed_args)
      ))
    return ['']

  return [(util.fixedbin(opcode, 5) + ''.join(args)).ljust(16, '0')]

# $var_name => expands variable
# $! => address of the current instruction
# @a => 97 => 1100001
# %fn => address of function/label 'fn'
# 123 => 1111011
def parse_arg(n, arg):
  sig = arg[0]
  val = arg[1:].decode('string_escape')

  if sig == '$':
    if val == '!':
      return '!'.ljust(8, '!')
    else:
      if not val in COMPILER_VARS:
        error(n, "undefined compiler variable referenced: " + val)
        return '0'
      else:
        return parse_arg(n, COMPILER_VARS[val])
  if sig == '@':
    return bin(ord(val))[2:]
  if sig == '%':
    if not val in COMPILER_LABELS:
      debug.log(" # label not yet defined: " + val)
      exec_compiler_instr(n, 'begin', [val])
    return ('%' + str(COMPILER_LABELS[val]['id'])).ljust(8, '%')
    
  return bin(int(arg, 10))[2:]

def exec_compiler_instr(line, instr, args):
  if instr in COMPILER_INSTRS:
    try:
      return COMPILER_INSTRS[instr]((line, instr, args), *args)
    except TypeError, e:
      error(line, ".end is missing a label name")
  else:
    error(line, "unknown compiler instruction: ", instr)
