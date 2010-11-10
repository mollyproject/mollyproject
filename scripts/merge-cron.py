#!/usr/bin/env python

import subprocess
import sys

cron = subprocess.Popen(["crontab", "-l"], stdout=subprocess.PIPE).communicate()[0].splitlines()

for line in sys.stdin:
    if line.rstrip() not in cron:
        cron.append(line.rstrip())

for line in cron:
    print line