from mutator import havoc

# 0th queue cycle
# 1. Put all input files into the queue
# 2. Run lzbench on all files in the queue without mutation, record performance numbers
# 3. Leave only one file per 10MB/s range
# 4. Save these original file-perf tuples somewhere else, or flag as original files

# 1st ~ nth queue cycle
# 1. Randomly select a file from the queue, mutate, and run lzbench
# 2. Put to the queue if unique value, otherwise discard

# TODO 1: Number of loops to run?
# TODO 2: Per one run, how many 'mutation+run's to perform?
# TODO 3: Do we run the feedback loop for all the files in the queue,
# or only for the files that are newly added to the queue?

# Assuming 
benchmark_dir = 'extracted_benchmarks/ZSTD-DECOMPRESS-1KB'
def main():
    pass
    
if __name__ == "__main__":
    main()