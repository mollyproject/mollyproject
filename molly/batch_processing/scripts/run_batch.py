#!/usr/bin/env python

import sys

from molly.batch_processing.utils import run_batch
    
if __name__ == '__main__':
    run_batch(*sys.argv[1:4])