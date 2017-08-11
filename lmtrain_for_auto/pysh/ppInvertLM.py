import sys
#===============================================
#Path setting
#===============================================
sys.path.insert(1, './')
sys.path.insert(2, './pylib/')


import os, sys, time, thread, logging, types, string
import libCorpusCell
import profile, pstats
import libTreeMerge
from ppLMToolKit import *
import ConfigParser

DEFAULT_BLOCK_SIZE      = 1000
DEFAULT_THREAD_NUM      = 7
DEFAULT_NEED_WRITE_ARPA = True
DEFAULT_TMP_PATH = "./tmp"
DEFAULT_BOW      = 0.0

class InvertConfig:
    def __init__(self, szConfigFile):
        cf=ConfigParser.ConfigParser()
        cf.read(szConfigFile)

        try:
            self.nBlockSize = cf.getint('global', 'BLOCK_SIZE')
        except:
            self.nBlockSize = DEFAULT_BLOCK_SIZE
            print 'BLOck SIZE not set use default value %d.'%(DEFAULT_BLOCK_SIZE)
        
        try:
            self.threadNum = cf.getint('global', 'THREAD_NUM')
        except:
            self.threadNum = DEFAULT_THREAD_NUM
            print 'Thread number not set use default value %d.'%(DEFAULT_THREAD_NUM)

        try:
            self.needWriteArpa = cf.getboolean('global', 'NEED_WRITE_ARPA')
        except:
            self.needWriteArpa = DEFAULT_NEED_WRITE_ARPA
        
        try:
            self.tmpPath = cf.get('global', 'TMP_PATH');
        except:
            self.tmpPath = DEFAULT_TMP_PATH;

        try:
            self.fDftBow = cf.getfloat('global', 'DEFAULT_BOW')
        except:
            self.fDftBow = DEFAULT_BOW
        
        self.nGramOrder = cf.getint('global', 'GRAM_ORDER')
        self.szLmKey    = cf.get('global', 'LM_KEY')
        self.szLexFile  = cf.get('global', 'LEX_FILE')


    def PrintConfig(self):
        print '----------------config start------------------'
        print 'BLOCK_SIZE     : ' + str(self.nBlockSize)
        print 'TMP_PATH       : ' + str(self.tmpPath)
        print 'THREAD_NUM     : ' + str(self.threadNum)
        print 'GRAM_ORDER     : ' + str(self.nGramOrder)
        print 'GRAM_KEY       : ' + self.szLmKey
        print 'LEX_FILE       : ' + self.szLexFile
        print 'NEED_WRITE_ARPA   : ' + str(self.needWriteArpa)
        print 'DEFAULT_BOW    : ' + str(self.fDftBow)
        print '----------------config end--------------------'


def InvertLM(config):
    m_InvertLM = CLMInvert(config.nGramOrder, \
            config.threadNum, config.tmpPath, config.nBlockSize, config.fDftBow)
    ret = m_InvertLM.LoadLexicon(config.szLexFile) 
    if ret != 0:
        raise RuntimeError, 'Load Lexicon failed.'

    ret = m_InvertLM.InvertLM(config.szLmKey, config.needWriteArpa)
    if ret != 0:
        raise RuntimeError, 'InvertLM failed.'


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise AttributeError, 'usage: python ppInvertLM.py config'

    config = InvertConfig(sys.argv[1])

    config.PrintConfig()

    tBeg = time.time()
    InvertLM(config)
    tInvert = time.time() - tBeg

    print 'Invert Success.'
    print '--------------------------------------------'
    print 'Invert time : %d s'%(tInvert)
    print '--------------------------------------------'
