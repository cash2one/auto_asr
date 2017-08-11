#/***************************************************************************
# * 
# * Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
# * 
# **************************************************************************/
# 
# 
# 
#/**
# * @file pysrc/ppBlockAdapt.py
# * @author jiangzhengxiang01(com@baidu.com)
# * @date 2014/04/10 17:30:14
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


class BlockAdaptConfig:
    def __init__(self, szConfigFile):
        cf = ConfigParser.ConfigParser()
        cf.read(szConfigFile)

        try:
            self.szInLm      = os.path.abspath(cf.get('global', 'IN_LM'))
        except:
            raise ValueError, 'input lm key not set.'

        try:
            self.szOutLm     = os.path.abspath(cf.get('global', 'OUT_LM'))
        except:
            raise ValueError, 'output lm key not set.'

        try:
            self.nBlockSize = cf.getint('global', 'DST_BLOCKSIZE')
        except:
            raise ValueError,'new block size not set.'

        try:
            self.nGramOrder = cf.getint('global', 'GRAM_ORDER')
        except:
            raise ValueError,'new block size not set.'

    def PrintConfig(self):
        print '----------------config start--------------------'
        print 'IN_LM              : ' + self.szInLm
        print 'OUT_LM             : ' + self.szOutLm
        print 'DST_BLOCKSIZE      : ' + str(self.nBlockSize)
        print 'GRAM_ORDER         : ' + str(self.nGramOrder)

def BlockAdapt(config):
    m_BlockAdapt = CBlockAdapt();

    ret = m_BlockAdapt.BlockAdapt(config.nGramOrder, config.nBlockSize, config.szInLm, config.szOutLm)
    if ret != 0:
        raise RuntimeError, 'BlockAdapt failed.'

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise AttibuteError, 'usage: python ppExpandDict.py config'

    config = BlockAdaptConfig(sys.argv[1])
    config.PrintConfig()
    
    tBeg = time.time()
    BlockAdapt(config)
    tExpand = time.time() - tBeg

    print 'BlockAdapt success.'
    print '------------------------------------'
    print 'BlockAdapt time : %d s'%(tExpand)
    print '------------------------------------'












#/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
