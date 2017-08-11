# -*- coding:utf8 -*-
'''
DATE: 2015/7/14

'''

import sys
import os
import re
import time

def main(input_pinyin_dict):

    pinyin2ph97 = {}

    for line in open('local/pinyin2ph97.map', 'r').xreadlines():
        line = line.strip()
        if not line:
            continue
        pinyin_ma,phones_ma = line.split('\t')
        
        pinyin2ph97[pinyin_ma] = phones_ma

    fpw_lex = open('data/local/lm/librispeech-lexicon.txt','w')

    only_words = {}
        
    for A_line in open(input_pinyin_dict, 'r').xreadlines():
        A_line = A_line.strip()
        if not A_line:
            continue
        
        A_line = re.sub('\(\d\)','',A_line)

        word,pinyins = A_line.split('\t')

        only_words[word] = ''

        fpw_lex.write(word + '\t')

        single_pinyins = pinyins.split(' ')

        ph97_phones = []

        for single_pinyin in single_pinyins:
            if pinyin2ph97.has_key(single_pinyin):
                ph97_phones.append(pinyin2ph97[single_pinyin])
            else:
                print word,single_pinyin

        ph97_phones_all = ' '.join('%s'% item for item in ph97_phones)

        fpw_lex.write(ph97_phones_all + '\n')

    fpw_lex.close()

    fpw_vocab = open('data/local/lm/librispeech-vocab.txt','w')

    for only_word in only_words:
        fpw_vocab.write(only_word + '\n')

    fpw_vocab.close()
        
                
if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        print "usage: python %s input_pinyin_dict" % sys.argv[0]
    else:
        main(sys.argv[1])
            

        

        

