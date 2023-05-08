class afl:
    def __init__(self):
        self.rand_seed = [0,0,0]
        self.rand_cnt = 0
        self.fixed_seed = 0
        self.init_seed = 0
    def rand_set_seed(self, init_seed):
        self.init_seed = init_seed
        #self.rand_seed[0] = hash64(self.init_seed, sizeof(init_seed), HASH_CONST)
        self.rand_seed[1] = self.rand_seed[0] ^ 0x1234567890abcdef
        self.rand_seed[2] = (self.rand_seed[0] & 0x1234567890abcdef) ^ (self.rand_seed[1] | 0xfedcba9876543210)
afl_struct = afl()