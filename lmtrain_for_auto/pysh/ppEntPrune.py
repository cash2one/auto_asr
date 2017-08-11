import sys, time, os
sys.path.insert(1, './')
sys.path.insert(2, './pylib/')
import ConfigParser
from ppLMToolKit import *
import shutil

DEFAULT_BLOCK_SIZE = 20000

class ppEntropyPrune:
    def Init(self, config):
        self.m_nGramOrder = config.nGramOrder

        self.m_EntPrune = CEntropyPrune()
        ret = self.m_EntPrune.Init(config.szLexFile, config.nOutLMVersion,
                config.nGramOrder, config.nBlockSize, config.szThreshold)
        if ret != 0:
            raise RuntimeError, 'Init ppEntropy failed.'

    def EntPrune(self, szInKey, szOutKey):
        if config.nOutLMVersion == 0:
            filename = szOutKey + '_' + str(config.nGramOrder) + '.lm'
            print "delete %s first."%(filename)
            if os.path.isfile(filename):
                os.remove(filename)
        else:
            dirname = szOutKey + '_' + str(config.nGramOrder)
            print "delete %s first."%(dirname)
            if os.path.isdir(dirname):
                shutil.rmtree(dirname)
            os.mkdir(dirname)
        
        ret = self.m_EntPrune.Prune(szInKey, szOutKey, config.nInLMVersion)
        if ret != 0:
            raise RuntimeError, 'Prune %s->%s failed.'%(szInKey, szOutKey)

class EntPruneConfig:
    def __init__(self, szConfigFile):
        cf = ConfigParser.ConfigParser()
        cf.read(szConfigFile)

        try:
            self.nBlockSize = cf.getint('global', 'BLOCK_SIZE')
        except:
            print 'Block size not set, use default value.'
            self.nBlockSize = DEFAULT_BLOCK_SIZE

        try:
            self.szLexFile = os.path.abspath(cf.get('global', 'LEX_FILE'))
        except:
            raise ValueError, 'Lex File not set.'

        try:
            self.nGramOrder = cf.getint('global', 'GRAM_ORDER')
        except:
            raise ValueError, 'Gram Order not set.'

        try:
            self.nInLMVersion = cf.getint('global', 'IN_LMVERSION')
        except:
            self.nInLMVersion = 0

        try:
            self.nOutLMVersion = cf.getint('global', 'OUT_LMVERSION')
        except:
            self.nOutLMVersion = 0

        try:
            szThreshold = cf.get('global', 'THRESHOLD')
	    print 'THRESHOLDARR: %s'%szThreshold
            self.szThreshold = szThreshold.replace(',', ' ')
        except:
            raise ValueError, 'Threshold not set.'

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
        print 'BLOCK_SIZE :%d'%self.nBlockSize
        print 'LEX_FILE   :%s'%self.szLexFile
        print 'GRAM_ORDER :%d'%self.nGramOrder
        print 'THRESHOLDARR  :%s'%self.szThreshold
        print 'INPUT_KEY  :%s'%self.szInKey
        print 'OUTPUT_KEY :%s'%self.szOutKey
        print '------------Configure End---------------'


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise AttributeError, 'usage: python ppEntPrune.py config'

    config = EntPruneConfig(sys.argv[1])
    config.PrintConfig()

    m_ppEntPrune = ppEntropyPrune()
    m_ppEntPrune.Init(config)

    tBeg = time.time()
    m_ppEntPrune.EntPrune(config.szInKey, config.szOutKey)
    tEntPrune = time.time() - tBeg

    print 'Entropy Prune success.'
    print '--------------------------------------------'
    print 'EntPrune time : %d s'%(tEntPrune)
    print '--------------------------------------------'
