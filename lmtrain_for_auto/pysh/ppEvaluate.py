import sys
sys.path.insert(1, './')
sys.path.insert(2, './pylib/')
import ConfigParser
import os
from ppLMToolKit import *
import error

logger = error.GetLogger()

class ppEvaluate:
    def __init__(self):
        self.m_Evaluate = CEvaluate()
        logger.info('Init ppEvaluate successfully.')
        
    def ComputePPL(self, szLmKey, szLexFn, nGramOrder, evalFile,szLmFsn, szOutFile):
        ret = self.m_Evaluate.Init(nGramOrder, szLmKey, szLexFn,szLmFsn)
        if ret != 0:
            raise RuntimeError, 'Init for m_Evaluate failed.'

        ret = self.m_Evaluate.ComputePPL(evalFile, szOutFile)
        if ret != 0:
            raise RuntimeError, 'Compute PPL for file %s failed.'%evalFile

        logger.info('Compute PPL success.')

class EvalConfig:
    def LoadConfig(self, szConfigFile):
        cf=ConfigParser.ConfigParser()
        cf.read(szConfigFile)

        try:
            self.szLmFsn = cf.get('global', 'LM_FSN')
        except:
            logger.warn('LM_FSN not set, default LM.')
            self.szLmFsn = 'LM'

        try:
            self.szOutFile = cf.get('global', 'OUT_FILE')
        except:
            raise ValueError, 'OUT_FILE not set.'

        try:
            self.szLmKey = cf.get('global', 'LM_KEY')
        except:
            raise ValueError, 'LM_KEY not set.'

        try:
            self.nGramOrder = cf.getint('global', 'GRAM_ORDER')
        except:
            raise ValueError, 'GRAM_ORDER not set.'

        try:
            self.szLexFile = os.path.abspath(cf.get('global', 'LEX_FILE'))
        except:
            raise ValueError, 'LEX_FILE not set.'

        try:
            self.szEvalFile = os.path.abspath(cf.get('global', 'EVAL_FILE'))
        except:
            raise ValueError, 'EVAL_FILE not set.'

        logger.info('Load config successful.')
        return 0

    def PrintConfig(self):
        logger.info('--------------------Config Start----------------------')
        logger.info('nGramOrder : %d'%(self.nGramOrder))
        logger.info('szLmKey    : %s'%(self.szLmKey))
        logger.info('szLmFsn    : %s'%(self.szLmFsn))
        logger.info('szLexFile  : %s'%(self.szLexFile))
        logger.info('szEvalFile : %s'%(self.szEvalFile))
        logger.info('--------------------Config End------------------------')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        logger.info('usage: python ppConvToFsn.py config')
        exit(-1)

    config = EvalConfig()
    ret = config.LoadConfig(sys.argv[1])
    if ret != 0:
        raise RuntimeError, 'Load config failed.'
    config.PrintConfig()

    eval = ppEvaluate()

    eval.ComputePPL(config.szLmKey, config.szLexFile, config.nGramOrder, config.szEvalFile,config.szLmFsn, config.szOutFile)

    logger.info('Evaluate successfully.')

