# Implementation of various mutation operators of AFLPlusPlus
import os
import afl
#from random_func import rand_below
from secrets import randbelow as rand_below
import struct

TWO_8 = 256
TWO_16 = 65536
TWO_32 = 4294967296

#interesting_8 = [-128, -1, 0, 1, 16, 32, 64, 100, 127]
interesting_8 = [128, 255, 0, 1, 16, 32, 64, 100, 127]
#interesting_16 = [-32768, -129, -128, 255, 256, 512, 1000, 1024, 4096, 32767]
interesting_16 = [32768, 65407, 65408, 255, 256, 512, 1000, 1024, 4096, 32767]
#interesting_32 = [-2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647]
interesting_32 = [2147483648, 4194304250, 4294934527, 32768, 65535, 65536, 100663045, 2147483647]

HAVOC_BLK_SMALL = 32
HAVOC_BLK_MEDIUM = 128
HAVOC_BLK_LARGE = 1500
HAVOC_BLK_XL = 32768
MAX_FILE = 1024 * 1024 #Max file size = 1MB

def choose_block_len(limit, queue_cycle=2, takes_too_long=False):
    # TODO: Need afl->queue_cycle and afl->run_over10m
    rlim = min(queue_cycle, 3)
    if takes_too_long:
        rlim = 1 # If it takes too long, choose a short block length
    x = rand_below(rlim)
    if x == 0:
        min_value = 1
        max_value = HAVOC_BLK_SMALL
    elif x == 1:
        min_value = HAVOC_BLK_SMALL
        max_value = HAVOC_BLK_MEDIUM
    else:
        if rand_below(10):
            min_value = HAVOC_BLK_MEDIUM
            max_value = HAVOC_BLK_LARGE
        else:
            min_value = HAVOC_BLK_LARGE
            max_value = HAVOC_BLK_XL
    if min_value >= limit:
        min_value = 1
    return min_value + rand_below(min(max_value, limit) - min_value + 1)

#def havoc(r, filename, afl_struct: afl):
def havoc(r, filename):
# 0~3: Flip a random bit
    if r in range(0, 4):
        # Open the file in binary mode
        with open(filename, "rb+") as f:
            # Print original contents ################ For debugging
            ########### file_contents = f.read()
            ########### print('Original contents:', file_contents) 

            # Get the size of the file in bits
            file_size_bits = os.path.getsize(filename) * 8
            # Pick a random bit position
            bit_pos = rand_below(file_size_bits)
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
            if file_size_bytes >= 4:
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
            data[byte_pos] = (data[byte_pos] - (rand_below(35)+1))%256
        else:
            data[byte_pos] = (data[byte_pos] + (rand_below(35)+1))%256
        with open(filename, "wb") as f:
            f.write(data)
# 24~25: Subtract 1~35 from a word(16b) (Little Endian)
# 26~27: Subtract 1~35 from a word(16b) (Big Endian)
# 28~29: Add 1~35 from a word(16b) (Little Endian)
# 30~31: Add 1~35 from a word(16b) (Big Endian)
    elif r in range(24, 32):
        with open(filename, 'rb+') as f:
            file_size_bytes = os.path.getsize(filename)
            if file_size_bytes >= 2:
                byte_pos = rand_below(file_size_bytes-1)
                f.seek(byte_pos)
                if r in range(24, 26):
                    new_data = ((struct.unpack('<H', f.read(2))[0] - rand_below(35)-1)%TWO_16).to_bytes(2, byteorder='little')
                elif r in range(26, 28):
                    new_data = ((struct.unpack('>H', f.read(2))[0] - rand_below(35)-1)%TWO_16).to_bytes(2, byteorder='big')
                elif r in range(28, 30):
                    new_data = ((struct.unpack('<H', f.read(2))[0] + rand_below(35)+1)%TWO_16).to_bytes(2, byteorder='little')
                else:
                    new_data = ((struct.unpack('>H', f.read(2))[0] + rand_below(35)+1)%TWO_16).to_bytes(2, byteorder='big')
                f.seek(byte_pos)
                f.write(new_data)
# 32~33: Subtract 1~35 from a dword(32b) (Little Endian)
# 34~35: Subtract 1~35 from a dword(32b) (Big Endian)
# 36~37: Add 1~35 from a dword(32b) (Little Endian)
# 38~39: Add 1~35 from a dword(32b) (Big Endian)
    elif r in range(32, 40):
        with open(filename, 'rb+') as f:
            file_size_bytes = os.path.getsize(filename)
            if file_size_bytes >= 4:
                byte_pos = rand_below(file_size_bytes-3)
                f.seek(byte_pos)
                if r in range(32, 34):
                    new_data = ((struct.unpack('<I', f.read(4))[0] - rand_below(35)-1)%TWO_32).to_bytes(4, byteorder='little')
                elif r in range(34, 36):
                    new_data = ((struct.unpack('>I', f.read(4))[0] - rand_below(35)-1)%TWO_32).to_bytes(4, byteorder='big')
                elif r in range(36, 38):
                    new_data = ((struct.unpack('<I', f.read(4))[0] + rand_below(35)+1)%TWO_32).to_bytes(4, byteorder='little')
                else:
                    new_data = ((struct.unpack('>I', f.read(4))[0] + rand_below(35)+1)%TWO_32).to_bytes(4, byteorder='big')
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
        if file_size_bytes + HAVOC_BLK_XL < MAX_FILE:
            clone_len = choose_block_len(file_size_bytes)
            clone_from = rand_below(file_size_bytes-clone_len+1)
            clone_to = rand_below(file_size_bytes)
            data[clone_to:clone_to+clone_len] = data[clone_from:clone_from+clone_len]
            with open(filename, "wb") as f:
                f.write(data)
# 47: Clone a particular byte clone_length times
# Output length increase by clone_length
# Case 1: repeat a value from 0~255
# Case 2: repeat a value from a random position of the file
    elif r == 47:
        with open(filename, "rb") as f:
            data = bytearray(f.read())
        file_size_bytes = len(data)
        if file_size_bytes + HAVOC_BLK_XL < MAX_FILE:
            clone_len = choose_block_len(HAVOC_BLK_XL)
            clone_to = rand_below(file_size_bytes)
            if rand_below(2) == 0:
                byte_to_clone = rand_below(256)
            else:
                byte_to_clone = data[rand_below(file_size_bytes)]
            data[clone_to:clone_to+clone_len] = [byte_to_clone]*clone_len
            with open(filename, "wb") as f:
                f.write(data)
# 48~50: Overwrite 'clone_length' bytes from 'clone_from' to 'clone_to'
# Output length same
    elif r in range(48,51):
        with open(filename, "rb") as f:
            data = bytearray(f.read())
        file_size_bytes = len(data)
        if file_size_bytes >= 2:
            copy_len = choose_block_len(file_size_bytes-1)
            copy_from = rand_below(file_size_bytes-copy_len+1)
            copy_to = rand_below(file_size_bytes-copy_len+1)
            if copy_from != copy_to:
                data[copy_to:copy_to+copy_len] = data[copy_from:copy_from+copy_len]
                with open(filename, "wb") as f:
                    f.write(data)
# 51: Repeat a particular byte like 47, but overwrite from a random position of the file
# Output length same
    elif r == 51:
        with open(filename, "rb") as f:
            data = bytearray(f.read())
        file_size_bytes = len(data)
        copy_len = choose_block_len(file_size_bytes-1)
        copy_to = rand_below(file_size_bytes-copy_len+1)
        if rand_below(2) == 0:
            byte_to_clone = rand_below(256)
        else:
            byte_to_clone = data[rand_below(file_size_bytes)]
        data[copy_to:copy_to+copy_len] = [byte_to_clone]*copy_len
        with open(filename, "wb") as f:
            f.write(data)
# 52: +1 to a byte
# 53: -1 to a byte
# 54: Flip a byte (^= 0xff)
    elif r in range(52,55):
        with open(filename, "rb") as f:
            data = bytearray(f.read())
        file_size_bytes = len(data)
        if r == 52:
            data[rand_below(file_size_bytes)] = (data[rand_below(file_size_bytes)]+1)%256
        elif r == 53:
            data[rand_below(file_size_bytes)] = (data[rand_below(file_size_bytes)]-1)%256
        else:
            data[rand_below(file_size_bytes)] ^= 0xff
        with open(filename, "wb") as f:
            f.write(data)
# 55~56: Switch bytes (len=choose_block_len(MIN(switch_len, to_end))
    elif r in range(55,57):
        with open(filename, "rb") as f:
            data = bytearray(f.read())
        file_size_bytes = len(data)
        if file_size_bytes >= 4:
            switch_from = rand_below(file_size_bytes)
            switch_to = -1
            while True:
                switch_to = rand_below(file_size_bytes)
                if switch_to != switch_from:
                    break
            switch_len = abs(switch_to - switch_from)
            to_end = file_size_bytes - max(switch_from, switch_to)
            switch_len = choose_block_len(min(switch_len, to_end))
            temp = data[switch_from:switch_from+switch_len]
            data[switch_from:switch_from+switch_len] = data[switch_to:switch_to+switch_len]
            data[switch_to:switch_to+switch_len] = temp
            with open(filename, "wb") as f:
                f.write(data)
# 57~64: Delete bytes (len=choose_block_len(temp_len-1))
    elif r in range(57,65):
        with open(filename, "rb") as f:
            data = bytearray(f.read())
        file_size_bytes = len(data)
        if file_size_bytes >= 256: # Lower bound on file size
            delete_len = choose_block_len(file_size_bytes//2 - 1) # Save at least half of the file
            delete_from = rand_below(file_size_bytes-delete_len+1)
            data[delete_from:delete_from+delete_len] = \
                data[delete_from+delete_len:file_size_bytes]
            with open(filename, "wb") as f:
                f.write(data[:file_size_bytes-delete_len])
# Default: Extra options. Not implemented in the file.
    else:
        pass

# def main():
#     # print('Hello World!')
#     # afl_struct = afl.afl_struct
#     # filename = 'test'
#     # havoc(11, filename, afl_struct)
    

# if __name__ == "__main__":
#     main()