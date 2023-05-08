# Implementation of various mutation operators of AFLPlusPlus
import os
import afl
#from random_func import rand_below
from secrets import randbelow as rand_below
import struct

interesting_8 = [-128, -1, 0, 1, 16, 32, 64, 100, 127]
interesting_16 = [-32768, -129, -128, 255, 256, 512, 1000, 1024, 4096, 32767]
interesting_32 = [-2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647]

HAVOC_BLK_SMALL = 32
HAVOC_BLK_MEDIUM = 128
HAVOC_BLK_LARGE = 1500
HAVOC_BLK_XL = 32768
MAX_FILE = 1024 * 1024 #Max file size = 1MB

def choose_block_len(limit):
    # TODO: Need afl->queue_cycle and afl->run_over10m


    # rlim = min(queue_cycle, 3)
    # If it takes too long, rlim=1
    # case with a random value of 0~rlim
    # 0: 1~Havoc_BLK_SMALL
    # 1: Havoc_BLK_SMALL~Havoc_BLK_MEDIUM
    # if random value between 0~9 is not 0, HAVOC_BLK_MEDIUM~HAVOC_BLK_LARGE
    # else HAVOC_BLK_LARGE~HAVOC_BLK_XL

    # if min>=limit --> min_value=1
    # return min_value + random value between 0~(min(max_value, limit)-min_value+1)

    
static inline u32 choose_block_len(afl_state_t *afl, u32 limit) {

  u32 min_value, max_value;
  u32 rlim = MIN(afl->queue_cycle, (u32)3);

  if (unlikely(!afl->run_over10m)) { rlim = 1; }

  switch (rand_below(afl, rlim)) {

    case 0:
      min_value = 1;
      max_value = HAVOC_BLK_SMALL;
      break;

    case 1:
      min_value = HAVOC_BLK_SMALL;
      max_value = HAVOC_BLK_MEDIUM;
      break;

    default:

      if (likely(rand_below(afl, 10))) {

        min_value = HAVOC_BLK_MEDIUM;
        max_value = HAVOC_BLK_LARGE;

      } else {

        min_value = HAVOC_BLK_LARGE;
        max_value = HAVOC_BLK_XL;

      }

  }

  if (min_value >= limit) { min_value = 1; }

  return min_value + rand_below(afl, MIN(max_value, limit) - min_value + 1);

}

def havoc(r, filename, afl_struct: afl):
# 0~3: Flip a random bit
    if r in range(0, 4):
        # Open the file in binary mode
        with open(filename, "rb+") as f:
            # Print original contents
            file_contents = f.read()
            print('Original contents:', file_contents) ################ For debugging

            # Get the size of the file in bits
            file_size_bits = os.path.getsize(filename) * 8
            # Pick a random bit position
            bit_pos = rand_below(file_size_bits)+1
            f.seek(bit_pos // 8)

            # Read the byte at the current position
            byte = ord(f.read(1))

            # Flip the desired bit
            byte ^= 1 << (bit_pos % 8)

            # Write the modified byte back to the file
            f.seek(-1, os.SEEK_CUR)
            f.write(bytes([byte]))
# 4~7: Change a byte(8b) to an interesting value
    elif r in range(4, 8):
        with open(filename, "rb") as f:
            data = bytearray(f.read())
        file_size_bytes = len(data)
        byte_pos = rand_below(file_size_bytes)
        data[byte_pos] = interesting_8[rand_below(len(interesting_8))]
        with open(filename, "wb") as f:
            f.write(data)
# 8~9: Change a word(16b) to an interesting value (Little Endian)
# 10~11: Change a word(16b) to an interesting value (Big Endian)
    elif r in range(8, 12):
        with open(filename, "r+b") as f:
            file_size_bytes = os.path.getsize(filename)
            if file_size_bytes >= 2:
            byte_pos = rand_below(file_size_bytes-1)
            if r in range(8, 9):
                new_data = interesting_16[rand_below(len(interesting_16))].to_bytes(2, byteorder='little')
            else:
                new_data = interesting_16[rand_below(len(interesting_16))].to_bytes(2, byteorder='big')
            f.seek(byte_pos)
            f.write(new_data)
# 12~13: Change a dword(32b) to an interesting value (Little Endian)
# 14~15: Change a dword(32b) to an interesting value (Big Endian)
    elif r in range(12, 16):
        with open(filename, "r+b") as f:
            file_size_bytes = os.path.getsize(filename)
            byte_pos = rand_below(file_size_bytes-3)
            if r in range(12, 13):
                new_data = interesting_32[rand_below(len(interesting_32))].to_bytes(4, byteorder='little')
            else:
                new_data = interesting_32[rand_below(len(interesting_32))].to_bytes(4, byteorder='big')
            f.seek(byte_pos)
            f.write(new_data)
# 16~19: Subtract 1~35 from a byte(8b)
# 20~23: Add 1~35 from a byte(8b)
    elif r in range(16, 24):
        with open(filename, "rb") as f:
            data = bytearray(f.read())
        file_size_bytes = len(data)
        byte_pos = rand_below(file_size_bytes)
        if r in range(16, 20):
            data[byte_pos] -= rand_below(35)+1
        else:
            data[byte_pos] += rand_below(35)+1
        with open(filename, "wb") as f:
            f.write(data)
# 24~25: Subtract 1~35 from a word(16b) (Little Endian)
# 26~27: Subtract 1~35 from a word(16b) (Big Endian)
# 28~29: Add 1~35 from a word(16b) (Little Endian)
# 30~31: Add 1~35 from a word(16b) (Big Endian)
    elif r in range(24, 32):
        with open(filename, 'rb+') as f:
            file_size_bytes = os.path.getsize(filename)
            byte_pos = rand_below(file_size_bytes-1)
            f.seek(byte_pos)
            if r in range(24, 26):
                new_data = (struct.unpack('<H', f.read(2))[0] - rand_below(35)-1).to_bytes(2, byteorder='little')
            elif r in range(26, 28):
                new_data = (struct.unpack('>H', f.read(2))[0] - rand_below(35)-1).to_bytes(2, byteorder='big')
            elif r in range(28, 30):
                new_data = (struct.unpack('<H', f.read(2))[0] + rand_below(35)+1).to_bytes(2, byteorder='little')
            else:
                new_data = (struct.unpack('>H', f.read(2))[0] + rand_below(35)+1).to_bytes(2, byteorder='big')
            f.seek(byte_pos)
            f.write(new_data)
# 32~33: Subtract 1~35 from a dword(32b) (Little Endian)
# 34~35: Subtract 1~35 from a dword(32b) (Big Endian)
# 36~37: Add 1~35 from a dword(32b) (Little Endian)
# 38~39: Add 1~35 from a dword(32b) (Big Endian)
    elif r in range(32, 40):
        with open(filename, 'rb+') as f:
            file_size_bytes = os.path.getsize(filename)
            byte_pos = rand_below(file_size_bytes-3)
            f.seek(byte_pos)
            if r in range(32, 34):
                new_data = (struct.unpack('<I', f.read(4))[0] - rand_below(35)-1).to_bytes(4, byteorder='little')
            elif r in range(34, 36):
                new_data = (struct.unpack('>I', f.read(4))[0] - rand_below(35)-1).to_bytes(4, byteorder='big')
            elif r in range(36, 38):
                new_data = (struct.unpack('<I', f.read(4))[0] + rand_below(35)+1).to_bytes(4, byteorder='little')
            else:
                new_data = (struct.unpack('>I', f.read(4))[0] + rand_below(35)+1).to_bytes(4, byteorder='big')
            f.seek(byte_pos)
            f.write(new_data)
# 40~43: Set a byte(8b) to a random value(1~255)
    elif r in range(40, 44):
        with open(filename, "rb") as f:
            data = bytearray(f.read())
        file_size_bytes = len(data)
        byte_pos = rand_below(file_size_bytes)
        data[byte_pos] = rand_below(255)+1
        with open(filename, "wb") as f:
            f.write(data)
# 44~46: Clone a certain number of bytes to another position
# New output: [0~clone_to, clone_from_clone_to, clone_to~file_size_bytes]
# Output length increase by clone_from~clone_to
    elif r in range(44, 47):
        with open(filename, "rb") as f:
            data = bytearray(f.read())
        file_size_bytes = len(data)

        pass
# 47: Clone a particular byte clone_length times
# Output length increase by clone_length
# Case 1: repeat a value from 0~255
# Case 2: repeat a value from a random position of the file
    elif r is 47:
        pass
# 48~50: Overwrite 'clone_length' bytes from 'clone_from' to 'clone_to'
# Output length same
    elif r in range(48,51):
        pass
# 51: Repeat a particular byte like 47, but overwrite from a random position of the file
# Output length same
    elif r is 51:
        pass
# 52: +1 to a byte
# 53: -1 to a byte
# 54: Flip a byte (^= 0xff)
    elif r in range(52,55):
        pass
# 55~56: Switch bytes (len=choose_block_len(MIN(switch_len, to_end))
    elif r in range(55,57):
        pass
# 57~64: Delete bytes (len=choose_block_len(temp_len-1))
    elif r in range(57,65):
        pass

# Default: Extra options. Not implemented in the file.
    else:
        pass

def main():
    print('Hello World!')
    afl_struct = afl.afl_struct
    filename = 'test'
    havoc(11, filename, afl_struct)
    

if __name__ == "__main__":
    main()