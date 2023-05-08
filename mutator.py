# Implementation of various mutation operators of AFLPlusPlus
import os
import afl
#from random_func import rand_below
from secrets import randbelow as rand_below
import struct

interesting_8 = [-128, -1, 0, 1, 16, 32, 64, 100, 127]
interesting_16 = [-32768, -129, -128, 255, 256, 512, 1000, 1024, 4096, 32767]
interesting_32 = [-2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647]
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

# 47: Clone a particular byte clone_length times
# Output length increase by clone_length
# Case 1: repeat a value from 0~255
# Case 2: repeat a value from a random position of the file

# 48~50: Overwrite 'clone_length' bytes from 'clone_from' to 'clone_to'
# Output length same

# 51: Repeat a particular byte like 47, but overwrite from a random position of the file
# Output length same

# 52: +1 to a byte
# 53: -1 to a byte
# 54: Flip a byte (^= 0xff)

# 55~56: Switch bytes (len=choose_block_len(MIN(switch_len, to_end))
# 57~64: Delete bytes (len=choose_block_len(temp_len-1))

def main():
    print('Hello World!')
    afl_struct = afl.afl_struct
    filename = 'test'
    havoc(11, filename, afl_struct)
    

if __name__ == "__main__":
    main()