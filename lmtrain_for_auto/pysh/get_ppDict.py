#/usr/bin/python

import os
import sys


args = sys.argv

if len(args) != 3:
    print('usage: get_ppDict.py vocab pplm.dict')
    exit(0)


zk_dict_file = open(args[1], 'r')
ppDict_file = open(args[2], 'w')

word_num = 0
word_list = []
for line in zk_dict_file:
    line = line.strip()
    if line == '<s>' or line == '</s>':
        continue
    word_num = word_num + 1
    word_list.append(line)
zk_dict_file.close()

#word_list.sort()
ppDict_file.write('%d\n'%word_num)

id = 1
for word in word_list:
    ppDict_file.write('%d\t%s\n'%(id, word))
    id = id + 1
ppDict_file.close()
