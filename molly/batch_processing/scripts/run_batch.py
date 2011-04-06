#!/usr/bin/env python

import sys

from molly.batch_processing import run_batch
    
if __name__ == '__main__':
    run_batch(sys.argv[1], sys.argv[2], sys.argv[3], False)