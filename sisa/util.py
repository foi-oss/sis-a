# "\x01" => "01"
def chr2binstr(char):
  return hex(ord(char))[2:].zfill(2)

# "11101" => 29
def binstr2int(bs):
  return int('0b' + bs, 2) if len(bs) >= 2 else 0

# fixedbin(1, 5) => "00001"
def fixedbin(n, f):
  return bin(n)[2:].zfill(f)

# partition_list([1,2,3,4,5,6,7,8,9], [3, 3, 3]) => [[1,2,3], [4,5,6], [7,8,9]]
def partition(xs, partitions):
  r = []
  n = 0
  for plen in partitions:
    r.append(xs[n:n+plen])
    n += plen
  return r

def chunks(l, n):
  for i in xrange(0, len(l), n):
      yield l[i:i+n]
      