# Python implementation of AFL++ random function
# Original C code from https://github.com/AFLplusplus/AFLplusplus

import random
import sys
import afl

RESEED_RNG = 2500000
UINT64_MAX = 18446744073709551615

#define ROTL(d, lrot) ((d << (lrot)) | (d >> (8 * sizeof(d) - (lrot))))

def rotl(d, lrot):
  return (d << (lrot)) | (d >> (8 * sys.getsizeof(d) - (lrot)))

def rand_next(afl: afl):
  xp = afl.rand_seed[0]
  afl.rand_seed[0] = 15241094284759029579 * afl.rand_seed[1]
  afl.rand_seed[1] = afl.rand_seed[1] - xp
  afl.rand_seed[1] = rotl(afl.rand_seed[1], 27)
  return xp

def rand_below(afl: afl, limit):
  if (limit <= 1):
    return 0

  if afl.rand_cnt is 0 and afl.fixed_seed is 0:
    afl.rand_cnt = (RESEED_RNG / 2) + (afl.rand_seed[1] % RESEED_RNG);
  afl.rand_cnt = afl.rand_cnt - 1

  unbiased_rnd = None
  while True:
    unbiased_rnd = rand_next(afl)
    if unbiased_rnd < (UINT64_MAX - (UINT64_MAX % limit)):
      break

  return unbiased_rnd % limit;
