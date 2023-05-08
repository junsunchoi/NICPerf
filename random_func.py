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

'''
#ifdef WORD_SIZE_64
// romuDuoJr
inline AFL_RAND_RETURN rand_next(afl_state_t *afl) {

  AFL_RAND_RETURN xp = afl->rand_seed[0];
  afl->rand_seed[0] = 15241094284759029579u * afl->rand_seed[1];
  afl->rand_seed[1] = afl->rand_seed[1] - xp;
  afl->rand_seed[1] = ROTL(afl->rand_seed[1], 27);
  return xp;

}

#else
// RomuTrio32
inline AFL_RAND_RETURN rand_next(afl_state_t *afl) {

  AFL_RAND_RETURN xp = afl->rand_seed[0], yp = afl->rand_seed[1],
                  zp = afl->rand_seed[2];
  afl->rand_seed[0] = 3323815723u * zp;
  afl->rand_seed[1] = yp - xp;
  afl->rand_seed[1] = ROTL(afl->rand_seed[1], 6);
  afl->rand_seed[2] = zp - yp;
  afl->rand_seed[2] = ROTL(afl->rand_seed[2], 22);
  return xp;

}

static inline u32 rand_below(afl_state_t *afl, u32 limit) {

  if (limit <= 1) return 0;

  /* The boundary not being necessarily a power of 2,
     we need to ensure the result uniformity. */
  if (unlikely(!afl->rand_cnt--) && likely(!afl->fixed_seed)) {

    ck_read(afl->fsrv.dev_urandom_fd, &afl->rand_seed, sizeof(afl->rand_seed),
            "/dev/urandom");
    // srandom(afl->rand_seed[0]);
    afl->rand_cnt = (RESEED_RNG / 2) + (afl->rand_seed[1] % RESEED_RNG);

  }

  /* Modulo is biased - we don't want our fuzzing to be biased so let's do it
   right. See:
   https://stackoverflow.com/questions/10984974/why-do-people-say-there-is-modulo-bias-when-using-a-random-number-generator
   */
  u64 unbiased_rnd;
  do {

    unbiased_rnd = rand_next(afl);

  } while (unlikely(unbiased_rnd >= (UINT64_MAX - (UINT64_MAX % limit))));

  return unbiased_rnd % limit;

}
'''