import sys
sys.path.insert(1, './')
sys.path.insert(2, './pylib/')
import ConfigParser
from ppLMToolKit import *

DEFAULT_FSN_VERSION = 1

class ppConvToFsn:
    def Init(self, config):
        self.m_ConvToFsn = CConvToFsn(config.nGramOrder)

        print 'Init ppConvToFsn successfully.'
        return 0
        
    def Convert(self, szLmKey, nFsnVersion):
        ret = self.m_ConvToFsn.Convert(szLmKey, nFsnVersion)
        if ret != 0:
            print 'Convert %s to FSN failed.'%szLmKey
            return -1

        print 'Convert %s successfully.'%(szLmKey)
        return 0

class ConvToFsnConfig:
    def LoadConfig(self, szConfigFile):
        cf=ConfigParser.ConfigParser()
        cf.read(szConfigFile)

        try:
            self.szLmKey = cf.get('global', 'LM_KEY')
        except:
            print 'LM_KEY not set.'
            return -1

        try:
            self.nGramOrder = cf.getint('global', 'GRAM_ORDER')
        except:
            print 'GRAM_ORDER not set.'
            return -1

        try:
            self.nFsnVersion   = cf.getint('global', 'FSN_VERSION')
        except:
            print 'FSN_VERSION not set, use default value %d.'%(DEFAULT_FSN_VERSION)
            self.nFsnVersion   = DEFAULT_FSN_VERSION

        print 'Load config successful.'
        return 0

    def PrintConfig(self):
        print '--------------------Config Start----------------------'
        print 'GRAM_ORDER : %d'%(self.nGramOrder)
        print 'FSN_VERSION: %d'%(self.nFsnVersion)
        print 'LM_KEY     : %s'%(self.szLmKey)
        print '--------------------Config End------------------------'

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'usage: python ppConvToFsn.py config'
        exit(-1)

    config = ConvToFsnConfig()
    ret = config.LoadConfig(sys.argv[1])
    if ret != 0:
        print 'Load config failed.'
        exit(-1)
    config.PrintConfig()

    convToFsn = ppConvToFsn()
    ret = convToFsn.Init(config)
    if ret != 0:
        print 'Init ppConvToFsn failed.'
        exit(-1)

    ret = convToFsn.Convert(config.szLmKey, config.nFsnVersion)
    if ret != 0:
        print 'Convert %s failed.'%(config.szLmKey)
        exit(-1)

    print 'Convert successfully.'

