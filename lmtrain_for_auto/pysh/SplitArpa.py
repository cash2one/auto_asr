#/usr/bin/python

import os
import sys
import re

args = sys.argv

file_name = args[1]

in_file = open(file_name, 'r')
pattern = re.compile('\\\\([\\d]+)-grams:')

gram_file = None
for line in in_file:
    m = pattern.match(line)
    if m != None:
        print(line)
        order = m.group(1)
        if gram_file != None:
            gram_file.close()
        gram_file = open('%s.%sgram'%(file_name, order), 'w')
        continue
    line = line.strip()
    if len(line) == 0:
        continue
    if line == '\\end\\':
        continue
    if gram_file != None:
        gram_file.write(line + '\n')
in_file.close()
