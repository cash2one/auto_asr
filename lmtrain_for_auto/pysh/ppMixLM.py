#/***************************************************************************
# * 
# * Copyright (c) 2011 Baidu.com, Inc. All Rights Reserved
# * 
# **************************************************************************/
 
 
 
#/**
# * @file pysrc/ppMixLM.adv.py
# * @author wanguanglu(com@baidu.com)
# * @date 2011/11/23 14:31:39
# * @brief 
# *  
# **/

import sys
#===============================================
#Path setting
#===============================================
sys.path.insert(1, './')
sys.path.insert(2, './pylib/')


import os, time, thread, logging, types, string
import math
import libCorpusCell
import profile, pstats
import libTreeMerge
import ConfigParser
from ppLMToolKit import *
import shutil

DEFAULT_BLOCK_SIZE = 20000
DEFAULT_LM_VERSION = 0

EPSILON = 0.00001

class ppMixLM:
    def __init__(self, config):
        self.nGramOrder= config.nGramOrder
        self.m_nLmVersion = config.nLmVersion
        self.m_ppMixLm = CPPMixLM()
        ret = self.m_ppMixLm.Init(config.szLexFile, 
                            config.nGramOrder, config.nBlockSize, self.m_nLmVersion)
        if ret != 0:
            raise RuntimeError('Init Mix lm class failed.')

    def MixLMList(self, lmlist, outkey):
        prelm = lmlist[0][0]
        preWeight = lmlist[0][1]

        if config.nLmVersion == 0:
            filename = config.szOutKey + '_' + str(config.nGramOrder) + '.lm'
            print "delete %s first."%(filename)
            if  os.path.isfile(filename):
                os.remove(filename)
        else:
            dirname = config.szOutKey + '_' + str(config.nGramOrder)
            print "delete %s first."%(dirname)
            if  os.path.isdir(dirname):
                shutil.rmtree(dirname)
            os.mkdir(dirname)
        
        for index in range(1, len(lmlist)):
            curlm = lmlist[index][0]
            curWeight = lmlist[index][1]
            self.MixLM(prelm, curlm, curWeight/(preWeight+curWeight), outkey)

            prelm = outkey
            preWeight = preWeight + curWeight

    def MixLM(self, lm1, lm2, lm2weight, outLm):
        print('%s %s %f -> %s'%(lm1, lm2, lm2weight, outLm))
        ret = self.m_ppMixLm.Mix(lm1, lm2, lm2weight, outLm, self.m_nLmVersion)
        if ret != 0:
            raise RuntimeError, 'Mix LM for %s and %s failed.'%(lm1, lm2)

class MixConfig:
    def __init__(self, szConfigFile):
        cf = ConfigParser.ConfigParser()
        cf.read(szConfigFile)

        try:
            self.nBlockSize = cf.getint('global', 'BLOCK_SIZE')
        except:
            print('Block size not set, use default value.')
            self.nBlockSize = DEFAULT_BLOCK_SIZE

        try:
            self.nLmVersion   = cf.getint('global', 'LM_VERSION')
        except:
            print 'LM_VERSION not set, use default value %d.'%(DEFAULT_LM_VERSION)
            self.nLmVersion   = DEFAULT_LM_VERSION

        try:
            self.szLexFile = os.path.abspath(cf.get('global', 'LEX_FILE'))
        except:
            raise ValueError, 'Lex file not set.'

        try:
            self.nGramOrder  = cf.getint('global', 'GRAM_ORDER')
        except:
            raise ValueError, 'Gram order not set.'

        try:
            self.szOutKey    = cf.get('global', 'OUT_KEY')
        except:
            raise ValueError, 'outKey not set.'

        self.mixlist = []
        lmlist = cf.items('lmlist')
        weightlist = cf.items('weightlist')
        if len(lmlist) != len(weightlist):
                raise ValueError, 'num of lmlist and weightlist not equal.'
                
        totweight = 0.0
        for index in range(len(lmlist)):
            if lmlist[index][0] != weightlist[index][0]:
                raise ValueError, 'key of lmlist and weightlist not equal.'

            lmitem = (lmlist[index][1], float(weightlist[index][1]))
            totweight = totweight + float(weightlist[index][1])
            self.mixlist.append(lmitem)

        if math.fabs(totweight-1) > EPSILON:
            raise ValueError, 'Total mixture weight is not 1.'



    def PrintConfig(self):
        print '------------configure start-----------'
        print 'BlockSize :%d'%self.nBlockSize
        print 'LexFile   :%s'%self.szLexFile
        print 'GramOrder :%d'%self.nGramOrder
        print 'mixlist:'
        print self.mixlist
        print 'szOutKey  :%s'%self.szOutKey
        print '------------configure end-------------'


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise AttributeError, 'usage: python ppMixLM.py config'

    config = MixConfig(sys.argv[1])

    config.PrintConfig()
    mixLm = ppMixLM(config)

    tBeg = time.time()
    mixLm.MixLMList(config.mixlist, config.szOutKey)
    tMix = time.time() - tBeg

    print 'Mix LM success.'
    print '--------------------------------------------'
    print 'mix time : %d s'%(tMix)
    print '--------------------------------------------'
