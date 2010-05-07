#!/usr/bin/env python

import sys

from molly.batch_processing.utils import run_batch
    
if __name__ == '__main__':
    sys.exit(run_batch(*sys.argv[1:4]) or 0)