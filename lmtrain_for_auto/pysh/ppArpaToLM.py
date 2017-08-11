#---------------------------------------------------------------
# Module: 	ppArpaToLM.py
# Function: Perfrom Arpa Convert to LM Operation
# Authoer:  Cao Lixin
# Date:	 	Dec.12, 2012
#---------------------------------------------------------------
import sys, time, os
#===============================================
#Path setting
#===============================================
sys.path.insert(1, './')
sys.path.insert(2, './pylib/')
import ConfigParser
from ppLMToolKit import *

class ppArpaToLM:
    def Init(self, config):
        self.m_nGramOrder = config.nGramOrder

        self.m_ArpaToLM = CArpaToLM()
        ret = self.m_ArpaToLM.Init(config.szLexFile, config.nGramOrder)
        if ret != 0:
            raise RuntimeError, 'Init ppArpaToLM failed.'

    def ArpaToLM(self, szInKey, szOutKey):
        ret = self.m_ArpaToLM.Convert(szInKey, szOutKey)
        if ret != 0:
            raise RuntimeError, 'Convert %s->%s failed.'%(szInKey, szOutKey)

class ArpaToLMConfig:
    def __init__(self, szConfigFile):
        cf = ConfigParser.ConfigParser()
        cf.read(szConfigFile)

        try:
            self.szLexFile = os.path.abspath(cf.get('global', 'LEX_FILE'))
        except:
            raise ValueError, 'Lex File not set.'

        try:
            self.nGramOrder = cf.getint('global', 'GRAM_ORDER')
        except:
            raise ValueError, 'Gram Order not set.'

        try:
            self.szInKey   = cf.get('global', 'IN_KEY')
        except:
            raise ValueError, 'Input Key not set.'

        try:
            self.szOutKey  = cf.get('global', 'OUT_KEY')
        except:
            raise ValueError, 'Output Key not set.'

        print 'Load config succesfully.'

    def PrintConfig(self):
        print '------------Configure Start-------------'
        print 'LEX_FILE   :%s'%self.szLexFile
        print 'GRAM_ORDER :%d'%self.nGramOrder
        print 'INPUT_KEY  :%s'%self.szInKey
        print 'OUTPUT_KEY :%s'%self.szOutKey
        print '------------Configure End---------------'


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise AttributeError, 'usage: python ppArpaToLM.py config'

    config = ArpaToLMConfig(sys.argv[1])
    config.PrintConfig()

    m_ppArpaToLM = ppArpaToLM()
    m_ppArpaToLM.Init(config)

    tBeg = time.time()
    m_ppArpaToLM.ArpaToLM(config.szInKey, config.szOutKey)
    tArpaToLM = time.time() - tBeg

    print 'Arpa Convert to LM Success.'
    print '--------------------------------------------'
    print 'ArpaToLM Time : %d s'%(tArpaToLM)
    print '--------------------------------------------'
