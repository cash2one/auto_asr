#/***************************************************************************
# * 
# * Copyright (c) 2012 Baidu.com, Inc. All Rights Reserved
# * 
# **************************************************************************/
 
#/**
# * @file ppDecreaseDict.py
# * @brief decrease dict. only the gram related to the new vocabulary are reserved. 
# * @author wanguanglu(com@baidu.com)
# * @date 2012/08/21 17:12:26
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


class DecreaseDictConfig:
    def __init__(self, szConfigFile):
        cf = ConfigParser.ConfigParser()
        cf.read(szConfigFile)

        try:
            self.szOriLexFile = os.path.abspath(cf.get('global', 'ORI_LEX_FILE'))
        except:
            raise ValueError, 'original lexicon file not set.'

        try:
            self.szNewLexFile = os.path.abspath(cf.get('global', 'NEW_LEX_FILE'))
        except:
            raise ValueError, 'new lexicon file not set.'

        try:
            self.szInLm      = os.path.abspath(cf.get('global', 'IN_LM'))
        except:
            raise ValueError, 'input lm key not set.'

        try:
            self.szOutLm     = os.path.abspath(cf.get('global', 'OUT_LM'))
        except:
            raise ValueError, 'output lm key not set.'

        try:
            self.nGramOrder = cf.getint('global', 'GRAM_ORDER')
        except:
            raise ValueError,'gram order not set.'

    def PrintConfig(self):
        print '----------------config start--------------------'
        print 'ORI_LEX_FILE       : ' + self.szOriLexFile
        print 'NEW_LEX_FILE       : ' + self.szNewLexFile
        print 'IN_LM              : ' + self.szInLm
        print 'OUT_LM             : ' + self.szOutLm
        print 'GRAM_ORDER         : ' + str(self.nGramOrder)

def DecreaseDict(config):
    m_DecreaseDict = CDecreaseDict();

    ret = m_DecreaseDict.DecreaseDict(config.szInLm, config.szOutLm, 
            config.szOriLexFile, config.szNewLexFile, config.nGramOrder)
    if ret != 0:
        raise RuntimeError, 'Decrease dict failed.'

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise AttibuteError, 'usage: python ppDecreaseDict.py config'

    config = DecreaseDictConfig(sys.argv[1])
    config.PrintConfig()
    
    tBeg = time.time()
    DecreaseDict(config)
    tDecrease = time.time() - tBeg

    print 'Decrease success.'
    print '------------------------------------'
    print 'Decrease time : %d s'%(tDecrease)
    print '------------------------------------'




#/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
