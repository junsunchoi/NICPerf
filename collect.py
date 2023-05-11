import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--algo", help="zstd or snappy", default="zstd", type=str)
parser.add_argument("--cord", help="compress or decompress", default="decompress", type=str)
parser.add_argument("--queue-cycles", help="Queue cycles for the whole benchmark files", \
                    default=10, type=int)
parser.add_argument("--n", help="Number of mutations to run per file", \
                    default=1, type=int)
parser.add_argument("--newonly", action='store_true', default=False)
args = parser.parse_args()
basedir = '/home/junsun2/fuzz/'
fuzz_result_path = basedir + 'result/' + args.algo + '_' + args.cord + '_' + \
    'cycle' + str(args.queue_cycles) + '_n' + str(args.n)
fuzz_result_path += '_newonly.csv' if args.newonly else '.csv'

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv(fuzz_result_path)
print(df)