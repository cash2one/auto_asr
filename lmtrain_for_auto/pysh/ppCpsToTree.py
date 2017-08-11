#---------------------------------------------------------------
#---------------------------------------------------------------
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
import shutil

DEFAULT_BLOCK_SIZE      = 20000
DEFAULT_GRAM_ORDER      = 3
DEFAULT_TXT_HAS_WEIGHT   = False
DEFAULT_SERVERS          = ()
DEFAULT_CPU_NUM          = 4

class ppCpsToTree:
    def __init__(self, config):
        self.m_nBlockSize = config.nBlockSize
        self.m_szTreeDir  = config.szTreeDir
        self.m_nGramOrder = config.nGramOrder
        self.m_nRealOrder = self.m_nGramOrder
        if self.m_nGramOrder == 2 or self.m_nGramOrder == 1:
            self.m_nGramOrder = self.m_nGramOrder + 1
        self.m_LexFile      = config.szLexFile

        self.txtHasWeight   = config.isTxtHasWeight
        self.ppservers      = config.m_Servers
        self.ncpus          = config.m_nCpuNum

        self.m_TrainLM      = CLMTrain()
            
        self.m_nVocSize      = self.m_TrainLM.LoadLexicon(self.m_LexFile)
        if self.m_nVocSize < 0:
            raise RuntimeError, 'Load Lexicon failed.'

        self.m_CorpusList = []  

        fp = open(config.szCpsList, 'rt')         
        for item in fp:
            item = item.strip()
            if len(item) == 0:
                continue
            self.m_CorpusList.append(item)
        fp.close()     

    def NextBlock(self):
        nCpsProcessed= self.m_ppComputeLib.SubmitCntTask(self.m_CorpusList)
        if nCpsProcessed < 0:
            raise RuntimeError, 'Submit count task failed.'
        return nCpsProcessed

    def ppNgramTreeObtain (self, wordIdSt, wordIdEd, nCurGram):
        """ parallel tree generation for the word interval [wordIdSt, wordIdEd] """
        
        FileList = []
        memFileList =  self.m_ppComputeLib.\
                SubmitObtTreeTask(wordIdSt, wordIdEd, nCurGram)
        if memFileList == None:
            raise RuntimeError, 'Obtain tree failed.'

        return memFileList

    def ChangeCorpusToTree (self):
        #process the corpus in self.m_CorpusList block by block
        blockNum = 0
        print "Begin to change corpus to tree..."

        if len(self.m_CorpusList) > 0:
            self.m_ppComputeLib = libCorpusCell.CorpusCell(self.ppservers, \
                    self.ncpus, self.txtHasWeight, self.m_LexFile)
            
            for szCorpusFl in self.m_CorpusList:
                szTreeDir = self.m_szTreeDir + os.sep + os.path.basename(szCorpusFl)
                
                if os.path.isfile(szTreeDir):
                    os.remove(szTreeDir)
                if os.path.isdir(szTreeDir):
                    shutil.rmtree(szTreeDir)
                os.mkdir(szTreeDir)

            while len(self.m_CorpusList) > 0:
                nCpsProcessed = self.NextBlock()
                if nCpsProcessed < 0:
                    raise RuntimeError, 'Next Block Failed.'
                if nCpsProcessed == 0:
                    print 'WARNING: no processer'
                    time.sleep(60)
                    continue

                wordidSt = 1
                while wordidSt < self.m_nVocSize:
                    wordidEd = wordidSt + self.m_nBlockSize -1
                    if wordidEd >= self.m_nVocSize:
                        wordidEd = self.m_nVocSize-1
                    for nGram in range(2,self.m_nGramOrder+1):
                        #create nGram tree
                        treeList = self.ppNgramTreeObtain (wordidSt, wordidEd, nGram)
                            
                        for cpsIdx in range(nCpsProcessed):
                            szTreeDir = self.m_szTreeDir + os.sep + \
                                    os.path.basename(self.m_CorpusList[cpsIdx])
                            FileName = szTreeDir + os.sep + 'cpstree' + '.' + \
                                    str(wordidSt) + '.' + str(wordidEd)  + '.' + str(nGram)
                            treeMem = MemFile()
                            if treeList[cpsIdx] == None or len(treeList[cpsIdx]) == 0:
                                continue

                            ret = treeMem.Init(treeList[cpsIdx], 0)
                            if ret != 0:
                                raise RuntimeError, "Init tree Mem failed."
                            treeMem.write(FileName)
                    wordidSt = wordidEd + 1

                self.m_CorpusList = self.m_CorpusList[nCpsProcessed:]
                blockNum = blockNum + 1
                print "No. %d block is finished!"%(blockNum)

#===============================================================================   
def CorpusToTreeParallel(config):
    print "Begin parallel change corus to tree ... "	
    tBeg = time.time()
    cpsToTree = ppCpsToTree(config)
    cpsToTree.ChangeCorpusToTree()

    tEnd = time.time()
    print "Total time for changing corus to tree = %d"%(tEnd-tBeg)    

class TrainConfig:
    def __init__(self, szConfigFile):
        cf=ConfigParser.ConfigParser()
        cf.read(szConfigFile)

        try:
            self.nBlockSize = cf.getint('global', 'BLOCK_SIZE')
        except:
            self.nBlockSize = DEFAULT_BLOCK_SIZE
            print 'BLOck SIZE not set use default value %d.'%(DEFAULT_BLOCK_SIZE)

        try:
            self.szCpsList = cf.get('global', 'CORPUS_LIST')
        except:
            raise ValueError, 'CORPUS LIST not set.'

        try:
            self.szTreeDir = cf.get('global', 'TREE_DIR')
        except:
            raise ValueError, 'TREE_DIR not set.'
        if self.szTreeDir[-1:] != '/':
            self.szTreeDir = self.szTreeDir + '/'


        try:
            self.szLexFile = cf.get('global', 'LEX_FILE')
        except:
            raise ValueError, 'LEX_FILE not set.'

        try:
            self.nGramOrder = cf.getint('global', 'GRAM_ORDER')
        except:
            self.nGramOrder = DEFAULT_GRAM_ORDER
            print 'GRAM_ORDER not set, use default value %d.'%(DEFAULT_GRAM_ORDER)

        try:
            self.isTxtHasWeight   = cf.getboolean('global', 'TEXT_HAS_WEIGHT')
        except:
            self.isTxtHasWeight   = DEFAULT_TXT_HAS_WEIGHT
            print 'TXT_HAS_WEIGHT not set, use default value ' + str(DEFAULT_TXT_HAS_WEIGHT)

        try:
            self.m_nCpuNum = cf.getint('global', 'CPU_NUM')
        except:
            self.m_nCpuNum = DEFAULT_CPU_NUM
            print 'CPU_NUM not set, use default value %d.'%(DEFAULT_CPU_NUM)
        
        try:
            serverLst = []
            for item in cf.items('ppservers'):
                serverLst.append(item[1])
            self.m_Servers = tuple(serverLst)
        except:
            self.m_Servers = DEFAULT_SERVERS
            print 'SERVERS not set, use default value.'
            print  DEFAULT_SERVERS

    def PrintConfig(self):
        print '----------------config start------------------'
        print 'nBlockSize     : %d.'%(self.nBlockSize)
        print 'szCpsList      : %s.'%(self.szCpsList)
        print 'szTreeDir      : %s.'%(self.szTreeDir)
        print 'szLexFile      : %s.'%(self.szLexFile)
        print 'nGramOrder     : %d.'%(self.nGramOrder)
        print 'isTxtHasWeight   : ' + str(self.isTxtHasWeight) + '.'
        print 'nCpuNum          : %d'%(self.m_nCpuNum)
        print 'ppservers        : '
        print self.m_Servers
        print '----------------config end--------------------'

#===============================================================================           
if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise AttributeError, 'usage: python ppCpsToTree.py config'

    config = TrainConfig(sys.argv[1])
    config.PrintConfig()

    tBeg = time.time()
    CorpusToTreeParallel (config)
    tCountTree = time.time() - tBeg

    print '--------------------------------------------'
    print 'Count tree successfully.'
    print 'Count Tree : %d s'%(tCountTree)
    print '--------------------------------------------'

