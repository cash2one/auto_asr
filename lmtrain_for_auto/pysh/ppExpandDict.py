#/***************************************************************************
# * 
# * Copyright (c) 2012 Baidu.com, Inc. All Rights Reserved
# * 
# **************************************************************************/
 
#/**
# * @file ppExpandDict.py
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
import shutil


class ExpandDictConfig:
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
            self.szInLm      = cf.get('global', 'IN_LM')
            #self.szInLm      = os.path.abspath(cf.get('global', 'IN_LM'))
        except:
            raise ValueError, 'input lm key not set.'

        try:
            #self.szOutLm     = os.path.abspath(cf.get('global', 'OUT_LM'))
            self.szOutLm     = cf.get('global', 'OUT_LM')
        except:
            raise ValueError, 'output lm key not set.'

        try:
            self.szLmVersion     = cf.get('global', 'LM_VERSION')
        except:
            raise ValueError, 'lm version not set.'

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
        print 'LM_VERSION         : ' + self.szLmVersion
        print 'GRAM_ORDER         : ' + str(self.nGramOrder)

def ExpandDict(config):
    dirname = config.szOutLm + "_" + str(config.nGramOrder)
    if  os.path.isdir(dirname):
            shutil.rmtree(dirname)
            os.mkdir(dirname)
    m_ExpandDict = CExpandDict();

    if config.szLmVersion == 'REV':
        ret = m_ExpandDict.ExpandDict(config.szInLm, config.szOutLm, 
            config.szOriLexFile, config.szNewLexFile, config.nGramOrder)
    elif config.szLmVersion == 'DSK':
        ret = m_ExpandDict.ExpandDictV1(config.szInLm, config.szOutLm, 
            config.szOriLexFile, config.szNewLexFile, config.nGramOrder)
    else:
        raise ValueError,'lm version not set.'
    if ret != 0:
        raise RuntimeError, 'Expand dict failed.'

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise AttibuteError, 'usage: python ppExpandDict.py config'

    config = ExpandDictConfig(sys.argv[1])
    config.PrintConfig()
    
    tBeg = time.time()
    ExpandDict(config)
    tExpand = time.time() - tBeg

    print 'Expand success.'
    print '------------------------------------'
    print 'Expand time : %d s'%(tExpand)
    print '------------------------------------'




#/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
