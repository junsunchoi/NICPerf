import os
import subprocess
import argparse
from secrets import randbelow as rand_below
import csv
from datetime import datetime
from mutator import havoc

# 0th queue cycle
# 1. Put all input files into the queue
# 2. Run lzbench on all files in the queue without mutation, record performance numbers
# 3. Save these original file-perf tuples somewhere else, or flag as original files

# 1st ~ nth queue cycle
# 1. Randomly select a file from the queue, mutate, and run lzbench
# 2. Put to the queue if unique value (Leave only one file per 10MB/s range),
# otherwise discard

# 1: Number of loops to run?
# --> Default 2, but can be changed by the user
# 2: Per one run, how many "mutation+run"s to perform?
# --> One.
# 3: Do we run the feedback loop for all the files in the queue,
# or only for the files that are newly added to the queue?
# --> Most recent mutation that resulted in unique performance per each original file

parser = argparse.ArgumentParser()
parser.add_argument("--algo", help="zstd or snappy", default="zstd", type=str)
parser.add_argument("--cord", help="compress or decompress", default="decompress", type=str)
parser.add_argument("--queue-cycles", help="Queue cycles for the whole benchmark files", \
                    default=2, type=int)
parser.add_argument("--n", help="Number of mutations to run per file", \
                    default=1, type=int)
parser.add_argument("--newonly", help="Whether to only run loop on newly found files or not", \
    action='store_true', default=False)
parser.add_argument("--bigfiles", help="If true, run loop on 4KB+ files. If false, run on 1KB files", \
    action='store_true', default=False)
parser.add_argument("--no-delete", help="Exclude deletion in havoc", \
    action='store_true', default=False)

args = parser.parse_args()

basedir = '/home/junsun2/fuzz/'
setting = ''
setting += ('ZSTD' if args.algo=='zstd' else 'Snappy')
setting += '-'
setting += ('COMPRESS' if args.cord=='compress' else 'DECOMPRESS')
setting += '-big' if args.bigfiles else '-1KB'
benchmark_dir = basedir + 'afl_in/' + setting
benchmark_dir_mutate = basedir + 'afl_in/mutate/newonly/' + setting \
    if args.newonly else \
    basedir + 'afl_in/mutate/' + setting

lzbench_binary_path = basedir + 'lzbench/lzbench'
lzbench_result_path = basedir + 'lzbench_result/' + args.algo + '_' + args.cord + '_' + \
    'cycle' + str(args.queue_cycles) + '_n' + str(args.n)
lzbench_result_path += ('_big_' if args.bigfiles else '_')
lzbench_result_path += 'lzbench_result' + ('newonly.log' if args.newonly else '.log')
fuzz_result_path = basedir + 'result/' + args.algo + '_' + args.cord + '_' + \
    'cycle' + str(args.queue_cycles) + '_n' + str(args.n)
if args.bigfiles:
    fuzz_result_path += '_big'
fuzz_result_path += '_newonly.csv' if args.newonly else '.csv'
file_queue_dict = dict()
perf_dict = dict()

# Algorithm should be a string all in small cases
# Return throughput and compression ratio
def run_lzbench(input_path, compress_or_decompress):
    if args.algo == 'zstd':
        comp_level = int(input_path.split('/')[-1].split('_')[1][2:])
        result = subprocess.run(\
        f"{lzbench_binary_path} -ezstd,{comp_level} -t1,1 -o4 {input_path} > {lzbench_result_path}", \
        shell=True)
    elif args.algo == 'snappy':
        result = subprocess.run(\
        f"{lzbench_binary_path} -esnappy -t1,1 -o4 {input_path} > {lzbench_result_path}", \
        shell=True)
    
    # lzbench_result.log format is like:
    # Compressor name,Compression speed,Decompression speed,Original size,Compressed size,Ratio,Filename
    # memcpy line
    # zstd 1.5.2 -1,101.11,253.59,1024,655,63.96,afl_in/ZSTD-DECOMPRESS/009999_cl1_ws10
    with open(lzbench_result_path, 'r') as file:
        lines = file.readlines()
        third_line = lines[2]
        throughput = 0.0
        if compress_or_decompress == 'compress':
            throughput = float(third_line.split(',')[1])
        else:
            throughput = float(third_line.split(',')[2])
        uncomp_size = int(third_line.split(',')[3])
        comp_ratio = float(third_line.split(',')[5])
        
    return throughput, comp_ratio, uncomp_size

def write_result(file_queue_dict):
    with open(fuzz_result_path, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(['original_file', 'throughput', 'uncomp_size', 'comp_ratio', 'comp_level', 'mutation_cycle'])
        for filename in file_queue_dict.keys():
            for file_perf_dict in file_queue_dict[filename]:
            # file_queue_dict[filename] is a list of dicts
                writer.writerow([file_perf_dict['original_file'], file_perf_dict['throughput'], \
                    file_perf_dict['uncomp_size'], file_perf_dict['comp_ratio'], \
                    file_perf_dict['comp_level'], file_perf_dict['mutation_cycle']])

def main():
    # Create a queue.
    # Each element is a list of dictionaries of the following format:
    # [original_file, throughput, uncomp_size, comp_ratio, comp_level, mutation cycle]
    # file_queue_dict = dict()

    # Create a list of performance numbers
    # Contain only 1 file per 10MB/s (ex: 100~110MB/s)
    # perf_dict = dict()
    new_file_count = 0

    filelist = os.listdir(benchmark_dir)
    subprocess.run(f"rm -rf {benchmark_dir_mutate}", shell=True)
    subprocess.run(f"mkdir {benchmark_dir_mutate}", shell=True)

    # Do for the 0th queue cycle
    print('Queue cycle: ', 0, datetime.now().time())
    filecount = 0
    for filename in filelist:
        filecount += 1
        if filecount % 1000 == 0:
            print('filecount is ', filecount, datetime.now().time())
        # filename is like '009488_cl1_ws10'
        comp_level = int(filename.split('_')[1][2:])
        filepath = benchmark_dir + '/' + filename
        throughput, uncomp_size, comp_ratio = run_lzbench(filepath, args.cord)
        perf_dict[int(throughput)//10] = throughput    
        file_queue_dict[filename] = \
            [{'original_file': filename, 
            'throughput': throughput, 
            'comp_ratio': comp_ratio, 
            'uncomp_size': uncomp_size, 
            'comp_level': comp_level,
            'mutation_cycle': 0}]
        subprocess.run(f"cp {benchmark_dir}/{filename} {benchmark_dir_mutate}/{filename}--0", \
            shell=True)
        
    # Backup the performance numbers of the original benchmark files
    perf_dict_original = perf_dict.copy()

    # Do for the 1th ~ nth queue cycle
    for queue_cycle in range(1, 1+args.queue_cycles):
        print('Queue cycle: ', queue_cycle, datetime.now().time())
        filecount = 0
        # For all files in the benchmark directory, do the following:
        # (Originally, we have to select random files from the benchmark directory)
        for filename in filelist:
            filecount += 1
            if filecount % 1000 == 0:
                print('filecount is ', filecount, datetime.now().time())
            
            # Select a file from the last queue cycle (most recent version)
            most_recent_filename = file_queue_dict[filename][-1]['original_file'] + '--' + \
                str(file_queue_dict[filename][-1]['mutation_cycle'])
            most_recent_filepath = benchmark_dir_mutate + '/' + most_recent_filename
            new_filename = file_queue_dict[filename][-1]['original_file'] + '--' + \
                str(queue_cycle)
            new_filepath = benchmark_dir_mutate + '/' + new_filename

            condition = (args.newonly and \
                file_queue_dict[filename][-1]['mutation_cycle']+1 == queue_cycle) or \
                (not args.newonly)
            if condition:
                # Copy the original file
                subprocess.run(f"cp {most_recent_filepath} {new_filepath}", \
                            shell=True)
                
                # Mutate the file n times
                for i in range(args.n):
                    if args.no_delete:
                        havoc(rand_below(57), new_filepath)
                    else:
                        havoc(rand_below(65), new_filepath)

                # Run lzbench on the new file
                comp_level = int(new_filename.split('_')[1][2:])
                # comp_level should match filename or most_recent_filename's split('_')[1][2:]
                throughput, comp_ratio, uncomp_size = run_lzbench(new_filepath, args.cord)

                # If the new file is unique, add to the queue
                # Otherwise, discard
                if int(throughput)//10 not in perf_dict.keys(): 
                    perf_dict[int(throughput)//10] = throughput
                    original_filename = file_queue_dict[filename][-1]['original_file']
                    assert filename==original_filename, "filename should match with original_filename"
                    file_queue_dict[filename].append(
                        {'original_file': original_filename, 
                        'throughput': throughput, 
                        'comp_ratio': comp_ratio, 
                        'uncomp_size': uncomp_size, 
                        'comp_level': comp_level,
                        'mutation_cycle': queue_cycle})
                    new_file_count += 1
                else:
                    subprocess.run(f"rm {new_filepath}", shell=True)

        # Checkpoint the results per every queue cycle
        print('New files found: ', new_file_count)
        write_result(file_queue_dict)
    
if __name__ == "__main__":
    main()
