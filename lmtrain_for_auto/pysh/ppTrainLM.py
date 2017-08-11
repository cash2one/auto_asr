#---------------------------------------------------------------
# Module: 	ppTrainLM.py
# Function: Perfrom parallel TrainLM Operation
# Authoer:  Jialei
# Date:	 	Nov.16, 2010
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

MOD_KN_SMOOTH = 'MOD_KN'
KATZ_SMOOTH   = 'KATZ'

DEFAULT_PARALLEL        = False
DEFAULT_BLOCK_SIZE      = 20000
DEFAULT_MAX_MEM_FOR_TREE_PRUN      = "30000000000"
DEFAULT_NEED_COUNT_TREE = True
DEFAULT_NEED_MERGE_TREE = True
DEFAULT_GRAM_ORDER      = 3
DEFAULT_MIN_COUNT_ARR   = [1, 1, 2, 2, 2, 2, 2, 2, 2]
DEFAULT_MAX_COUNT_ARR   = [1, 7, 7, 7, 7, 7, 7, 7, 7]
DEFAULT_SMOOTH_TYPE     = KATZ_SMOOTH
DEFAULT_WEIGHT_THRESHOLD = 0.0
DEFAULT_TXT_HAS_WEIGHT   = False
DEFAULT_LM_VERSION = 0

DEFAULT_SERVERS          = ()
DEFAULT_CPU_NUM          = 4

#-------------------------------
#       ppTrainLM
#-------------------------------
class ppTrainLM:
    def __init__(self, config):
        nRet = 0

        # resource file
        self.m_nGramOrder     = config.nGramOrder
        self.m_nRealOrder     = config.nRealOrder
        self.m_LexFile        = config.szLexFile

        # read corpus list from corpusDb
        self.m_CorpusList = []  

        fp = open(config.szCpsList, 'rt')         
        for item in fp:
            item = item.strip()
            if len(item) == 0:
                continue
            self.m_CorpusList.append(item)
        fp.close()     
        
        self.m_TrainLM      = CLMTrain()
        
        self.m_nVocSize     = self.m_TrainLM.LoadLexicon(self.m_LexFile)
        if self.m_nVocSize < 0:
            raise RuntimeError, 'Load Lexicon failed.'
        
        self.m_TrainLM.Init (self.m_nRealOrder, self.m_nGramOrder, config.szMinCountArr, config.szOutputKey,\
                             config.szMaxCountArr, config.szSmoothType)

        nRet = self.m_TrainLM.SetWeightThreshold(config.fWeightThreshold, config.szPrunWordList)
        if nRet == RET_ERROR:
            raise RuntimeError, 'SetWeightThreshold Failed.'

        self.m_txtHasWeight = config.isTxtHasWeight
        self.m_nBlockSize   = config.nBlockSize
        self.m_nMaxMemForTreePrun   = config.nMaxMemForTreePrun
        self.m_szTreeDir    = config.szTreeDir
        self.m_szOutputKey  = config.szOutputKey
        self.m_szTreeDir    = config.szTreeDir
        self.m_szMergeDir   = config.szMergeDir
        self.m_nLmVersion = config.nLmVersion


    def InitCmptCellForSeq(self):
        self.m_CmptCellList = []
        for szCorpusFl in self.m_CorpusList:
            print 'InitCmptCellForSeq: Build index for corpus %s'%szCorpusFl
            curCmptCell = LMCountCell()
            if self.m_txtHasWeight:
                ret = curCmptCell.__setstate_SenWt__(self.m_LexFile, szCorpusFl)
                if ret != 0:
                    raise RuntimeError, 'setstate_senWt failed.'
            else:
                ret = curCmptCell.__setstate__(self.m_LexFile, szCorpusFl)
                if ret != 0:
                    raise RuntimeError, 'setstate failed.'

            self.m_CmptCellList.append(curCmptCell)
    
    def MergeMemFile(self, FileList):
        """ merge memory file"""
        while 1:
            FileNum = len(FileList)
            if FileNum == 1: break   
            for ii in xrange(FileNum/2):
                file1 = FileList.pop(0)
                file2 = FileList.pop(0)
                mergedFile = MemFile()
                ret = mergedFile.merge(file1, file2)
                if ret != 0:
                    raise RuntimeError, 'Merge File failed.'
                FileList.append(str(mergedFile))
        memFile = MemFile()
        memFile.Init(FileList[0], 0)
        return memFile
        
    def SeqNgramTreeObtain (self, wordIdSt, wordIdEd, nCurGram):
        """ create tree in sequence for the word interval [wordIdSt, wordIdEd]"""
        #get string input 
        FileList = []
        #get string output
        for cmpt in self.m_CmptCellList:
            if self.m_txtHasWeight:
                File = cmpt.GetCellPyOutput_SenWt(wordIdSt, wordIdEd, nCurGram)
                if File == None:
                    raise RuntimeError, 'GetCellPyOutput_SenWt failed.'
            else:
                File = cmpt.GetCellPyOutput(wordIdSt, wordIdEd, nCurGram)
                if File == None:
                    raise RuntimeError, 'GetCellPyOutput failed.'
            FileList.append (File)
        return FileList
                              
    def GetDiscntState(self):
        "Statics discount info..."

        print "Statics discount info..."
        wordidSt = 1
        while wordidSt < self.m_nVocSize:
            wordidEd = wordidSt + self.m_nBlockSize -1
            if wordidEd >= self.m_nVocSize:
                wordidEd = self.m_nVocSize-1

            if(self.m_nRealOrder == 1):
                nGram = 2
                treeList = self.SeqNgramTreeObtain (wordidSt, wordidEd, nGram)
                tree     = self.MergeMemFile (treeList)
                ret = self.m_TrainLM.StaDiscntState(str(tree), nGram-1);
                if ret != 0:
                    raise RuntimeError('StaDiscntState for [order:%d]\
                            [wordidSt:%d][wordidEd:%d] failed.'\
                            %(nGram-1, wordidSt, wordidEd))
                wordidSt = wordidEd + 1
                continue

            for nGram in range(2, self.m_nRealOrder+1):
                #create nGram tree
                treeList = self.SeqNgramTreeObtain (wordidSt, wordidEd, nGram)
                tree     = self.MergeMemFile (treeList)
                self.m_TrainLM.StaDiscntState(str(tree), nGram-1);
                if nGram == self.m_nRealOrder:
                    ret = self.m_TrainLM.StaDiscntState(str(tree), nGram);
                    if ret != 0:
                        raise RuntimeError('StaDiscntState for [order:%d]\
                            [wordidSt:%d][wordidEd:%d] failed.'\
                            %(nGram-1, wordidSt, wordidEd))
            wordidSt = wordidEd + 1

        print 'compute discount coefficient'
        ret = self.m_TrainLM.InitialDiscounts()
        if ret != 0:
            raise RuntimeError, 'InitialDiscounts failed.'

    def GetDiscntStateFromTreeFiles (self):
        "Statics discount info..."

        print "Statics discount info..."
        wordidSt = 1
        while wordidSt < self.m_nVocSize:
            wordidEd = wordidSt + self.m_nBlockSize -1
            if wordidEd >= self.m_nVocSize:
                wordidEd = self.m_nVocSize-1
            
            if(self.m_nRealOrder == 1):
                nGram = 2
                FileName = self.m_szMergeDir + 'merge.' + \
                            str(wordidSt) + '.' + str(wordidEd)  + '.' + str(nGram)
                tree    = MemFile()
                tree.read    (FileName)
                ret = self.m_TrainLM.StaDiscntState(str(tree), nGram-1);
                if ret != 0:
                    raise RuntimeError('StaDiscntState for [order:%d]\
                            [wordidSt:%d][wordidEd:%d] failed.'\
                            %(nGram-1, wordidSt, wordidEd))
                wordidSt = wordidEd + 1
                continue

            for nGram in range(2,self.m_nRealOrder+1):
                #create nGram tree
                FileName = self.m_szMergeDir + 'merge.' + \
                            str(wordidSt) + '.' + str(wordidEd)  + '.' + str(nGram)
                tree    = MemFile()
                tree.read    (FileName)

                ret = self.m_TrainLM.StaDiscntState(str(tree), nGram-1);
                if ret != 0:
                    raise RuntimeError('StaDiscntState for [order:%d]\
                            [wordidSt:%d][wordidEd:%d] failed.'\
                            %(nGram-1, wordidSt, wordidEd))
                if nGram == self.m_nRealOrder:
                    ret = self.m_TrainLM.StaDiscntState(str(tree), nGram);
                    if ret != 0:
                        raise RuntimeError('StaDiscntState for [order:%d]\
                            [wordidSt:%d][wordidEd:%d] failed.'\
                            %(nGram-1, wordidSt, wordidEd))
            wordidSt = wordidEd + 1
                
        ret = self.m_TrainLM.InitialDiscounts()
        if ret != 0:
            raise RuntimeError, 'InitialDiscounts failed.'
                  
    def TrainUniGram(self):
        """Train Unigram LM model"""
        print "Begin to train unigram..."
        wordidSt = 1
        while wordidSt < self.m_nVocSize:
            wordidEd = wordidSt + self.m_nBlockSize -1
            if wordidEd >= self.m_nVocSize:
                wordidEd = self.m_nVocSize-1

            # create unigram tree
            treeList = self.SeqNgramTreeObtain (wordidSt, wordidEd, 2)
            tree     = self.MergeMemFile (treeList)
            # accu
            self.m_TrainLM.AccuUnigramCounts(str(tree));           
            wordidSt = wordidEd + 1

        #update   
        ret = self.m_TrainLM.UpdateUnigram()
        if ret != 0:
            raise RuntimeError('Update Unigram failed.')

    def TrainUniGramFromTreeFiles (self):
        """Train Unigram LM model"""
        print "Begin to train unigram..."

        wordidSt = 1
        while wordidSt < self.m_nVocSize:
            wordidEd = wordidSt + self.m_nBlockSize -1
            if wordidEd >= self.m_nVocSize:
                wordidEd = self.m_nVocSize-1

            print "Block unigram begin (wordidSt= %d wordidEd = %d totalWord = %d)!"\
                                    %(wordidSt, wordidEd, self.m_nVocSize)
            #read ngram tree from file
            nGram    = 2
            FileName = self.m_szMergeDir + 'merge.' + \
                           str(wordidSt) + '.' + str(wordidEd)  + '.' + str(nGram)
            if os.path.isfile(FileName):
                tree = MemFile()
                ret = tree.read(FileName)
                if ret != 0:
                    raise 'Read Tree failed.'
            else:
                raise 'Merge file not exist.'
            
            # accu
            self.m_TrainLM.AccuUnigramCounts(str(tree));           
            wordidSt = wordidEd + 1

        #update   
        self.m_TrainLM.UpdateUnigram()
                
    def TrainNGram(self):
        """Train Ngram LM model"""

        ret = self.m_TrainLM.InitWriteResultLM(self.m_szOutputKey, self.m_nLmVersion)
        if ret != 0:
            raise RuntimeError, 'Init Write Result Lm failed.'

        wordidSt = 1
        while wordidSt < self.m_nVocSize:
            wordidEd = wordidSt + self.m_nBlockSize -1
            if wordidEd >= self.m_nVocSize:
                wordidEd = self.m_nVocSize-1

            print 'Block N-gram begin (wordidSt= %d wordidEd = %d totalWord = %d)!'\
                    %(wordidSt, wordidEd, self.m_nVocSize)
            for nGram in range(2,self.m_nGramOrder+1):
                treeList = self.SeqNgramTreeObtain (wordidSt, wordidEd, nGram)
                tree     = self.MergeMemFile (treeList)
                ret = self.m_TrainLM.SetTree (str(tree), nGram);
                if ret != 0:
                    raise RuntimeError, 'Set Tree failed.'
                del tree
            #recursive train tree                    
            firstLyNdNum = self.m_TrainLM.RecurTrainNgram() 
            if firstLyNdNum < 0:
                raise RuntimeError, 'RecurTrainNgram failed.'
            ret         = self.m_TrainLM.ConvertLMFormate(firstLyNdNum)
            if ret != 0:
                raise RuntimeError, 'Convert LMFormat failed.'
            ret = self.m_TrainLM.WritePartResultLM(self.m_szOutputKey)
            if ret != 0:
                raise RuntimeError, 'WritePartResultLm failed.'
            wordidSt = wordidEd + 1

        self.m_TrainLM.SetBlockSize(self.m_nBlockSize)
        ret = self.m_TrainLM.EndWriteResultLM(self.m_szOutputKey)
        if ret != 0:
            raise RuntimeError, 'EndWriteResultLM failed.'

    def TrainNGramFromTreeFiles (self):
        """Train Ngram LM model"""
        self.m_TrainLM.InitWriteResultLM(self.m_szOutputKey, self.m_nLmVersion)
        treeMergeTime = 0;

        wordidSt = 1
        while wordidSt < self.m_nVocSize:
            wordidEd = wordidSt + self.m_nBlockSize -1
            if wordidEd >= self.m_nVocSize:
                wordidEd = self.m_nVocSize-1

            #read ngram trees from file           
            print "Block N-gram begin (wordidSt= %d wordidEd = %d totalWord = %d)!"\
                                        %(wordidSt, wordidEd, self.m_nVocSize)
            time1 = time.time()
            for nGram in range(2,self.m_nGramOrder+1):
                
                FileName = self.m_szMergeDir + 'merge.' + \
                            str(wordidSt) + '.' + str(wordidEd)  + '.' + str(nGram)
                if  os.path.isfile(FileName):
                    tree = MemFile()
                    ret = tree.read(FileName)
                    if ret != 0:
                        raise RuntimeError, 'read tree failed.'
                else:
                    raise RuntimeError, 'tree file not exist.'
                        
                self.m_TrainLM.SetTree (str(tree), nGram);
                del tree
            time2 = time.time()
            treeMergeTime += time2-time1
                                     
            #recursive train tree           
            firstLyNdNum = self.m_TrainLM.RecurTrainNgram() 
            nRet         = self.m_TrainLM.ConvertLMFormate(firstLyNdNum)
            if nRet == RET_ERROR:  
                wordidSt = wordidEd + 1
                continue
            self.m_TrainLM.WritePartResultLM(self.m_szOutputKey)
            wordidSt = wordidEd + 1
            
        self.m_TrainLM.SetBlockSize(self.m_nBlockSize)
        self.m_TrainLM.EndWriteResultLM(self.m_szOutputKey)
        if ret != 0:
            raise RuntimeError, 'EndWriteResultLM failed.'
        #self.m_TrainLM.PrintLM(self.m_szOutputKey)
        print "Total tree merge time = %d"%(treeMergeTime)
                
class ppCpsToTree:
    def __init__(self, config):
        self.m_nBlockSize = config.nBlockSize
        self.m_szTreeDir  = config.szTreeDir
        self.m_nGramOrder = config.nGramOrder
        self.m_nRealOrder = config.nRealOrder
        self.m_LexFile      = config.szLexFile

        self.txtHasWeight   = config.isTxtHasWeight
        self.ppservers      = config.m_Servers
        self.ncpus          = config.m_nCpuNum

        self.m_TrainLM      = CLMTrain()
        
        self.m_nVocSize      = self.m_TrainLM.LoadLexicon(self.m_LexFile)
        if self.m_nVocSize < 0:
            raise RuntimeError, 'Load Lexicon failed.'
        
        ret = self.m_TrainLM.Init (self.m_nRealOrder, self.m_nGramOrder, config.szMinCountArr, config.szOutputKey,
                             config.szMaxCountArr, config.szSmoothType)
        if ret != 0:
            raise RuntimeError, 'Init m_TrainLM failed.'
            

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

class ppMergeTree:
    def __init__(self, config):
        self.m_nBlockSize   = config.nBlockSize
        self.m_nMaxMemForTreePrun   = config.nMaxMemForTreePrun
        self.m_szTreeDir    = config.szTreeDir
        self.m_szMergeDir   = config.szMergeDir
        self.m_nGramOrder   = config.nGramOrder
        self.m_nRealOrder   = config.nRealOrder
        self.m_LexFile      = config.szLexFile

        self.ppservers      = config.m_Servers
        self.ncpus          = config.m_nCpuNum

        self.m_TrainLM      = CLMTrain()
        
        self.m_nVocSize      = self.m_TrainLM.LoadLexicon(self.m_LexFile)
        if self.m_nVocSize < 0:
            raise RuntimeError, 'Load Lexicon failed.'
        
        ret = self.m_TrainLM.Init (self.m_nRealOrder, self.m_nGramOrder, config.szMinCountArr, \
                    config.szOutputKey, config.szMaxCountArr, config.szSmoothType)
        if ret != 0:
            raise RuntimeError, 'Init m_TrainLM failed.'


        self.m_CorpusList = []  

        fp = open(config.szCpsList, 'rt')         
        for item in fp:
            while item[-1:] in ['\n', '\t', ' ']:   item = item[0 : len(item)-1]
            self.m_CorpusList.append(os.path.basename(item))
        fp.close()

        self.m_ppMerge = libTreeMerge.ppTreeMerge(config.m_nCpuNum, config.nMaxMemForTreePrun)

    def MergeTree(self):
        #remove current file.
        for file in os.listdir(self.m_szMergeDir):
            os.remove(self.m_szMergeDir + os.sep + file)

        wordidSt = 1
        while wordidSt < self.m_nVocSize:
            wordidEd = wordidSt + self.m_nBlockSize -1
            if wordidEd >= self.m_nVocSize:
                wordidEd = self.m_nVocSize-1
            for nGram in range(2, self.m_nGramOrder+1):
                for corpusName in self.m_CorpusList:
                    FileName = self.m_szTreeDir + os.sep + corpusName + os.sep + 'cpstree.' + \
                                str(wordidSt) + '.' + str(wordidEd)  + '.' + str(nGram)
                    if os.path.isfile(FileName):
                        curFile    = MemFile()
                        curFile.read    (FileName)
                        self.m_ppMerge.pp_submit(str(curFile))
                [key, result]   = self.m_ppMerge.GetPPresult()

                if len(result) == 0:
                    raise RuntimeError, 'tree list empty.'

                tree = MemFile()
                ret = tree.Init(result[0], 0)
                if ret != 0:
                    raise RuntimeError, 'Init Tree for %d_%d failed.'%(wordidSt, wordidEd)
                FileName = self.m_szMergeDir + os.sep + 'merge.' + \
                                str(wordidSt) + '.' + str(wordidEd)  + '.' + str(nGram)
                ret = tree.write(FileName)
                if ret != 0:
                    raise RuntimeError, 'write failed.'
            wordidSt = wordidEd + 1
                

#===============================================================================   
def TrainSeq(config):
    print "Begin sequal training ... "	

    if config.nLmVersion == 0:
        filename = config.szOutputKey + '_' + str(config.nGramOrder) + '.lm'
        print "delete %s first."%(filename)
        if  os.path.isfile(filename):
            os.remove(filename)
    else:
        dirname = config.szOutputKey + '_' + str(config.nGramOrder)
        print "delete %s first."%(dirname)
        if  os.path.isdir(dirname):
            shutil.rmtree(dirname)
        os.mkdir(dirname)

    tBeg = time.time()
    Tr = ppTrainLM(config)

    Tr.InitCmptCellForSeq()
    tBegTr = time.time()
    Tr.GetDiscntState()
    Tr.TrainUniGram()     
    if(Tr.m_nRealOrder == 1):
        Tr.m_TrainLM.InitWriteResultLM(Tr.m_szOutputKey)
        Tr.m_TrainLM.EndWriteResultLM(Tr.m_szOutputKey)
        tEnd = time.time()      
        print "Total time for train with tree = %d"%(tEnd-tBeg)  
    else:
        Tr.TrainNGram ()
    tEnd = time.time()
    print "train time without copus index = %d"%(tEnd-tBegTr)  
    print "Total time = %d"%(tEnd-tBeg)  

def CorpusToTreeParallel(config):
    print "Begin parallel change corus to tree ... "	
    tBeg = time.time()
    cpsToTree = ppCpsToTree(config)
    cpsToTree.ChangeCorpusToTree()

    tEnd = time.time()
    print "Total time for changing corus to tree = %d"%(tEnd-tBeg)    

def MergeTreeParallel(config):
    print 'Begin Merge Tree.'
    ppMerge = ppMergeTree(config)
    ppMerge.MergeTree()

def TrainWithTree (cofig):
    print "Begin train with tree ... "	

    if config.nLmVersion == 0:
        filename = config.szOutputKey + '_' + str(config.nGramOrder) + '.lm'
        print "delete %s first."%(filename)
        if os.path.isfile(filename):
            os.remove(filename)
    else:
        dirname = config.szOutputKey + '_' + str(config.nGramOrder)
        print "delete %s first."%(dirname)
        if os.path.isdir(dirname):
            shutil.rmtree(dirname)
        os.mkdir(dirname)

    tBeg = time.time()
    ppMerge = libTreeMerge.ppTreeMerge(config.m_nCpuNum, config.nMaxMemForTreePrun)   #set ncups for parallel tree merge
    Tr = ppTrainLM (config)
    Tr.GetDiscntStateFromTreeFiles ()
    Tr.TrainUniGramFromTreeFiles   ()
    if(Tr.m_nRealOrder == 1):
        Tr.m_TrainLM.InitWriteResultLM(Tr.m_szOutputKey)
        Tr.m_TrainLM.EndWriteResultLM(Tr.m_szOutputKey)
        #Tr.m_TrainLM.PrintLM(Tr.m_szOutputKey)
        tEnd = time.time()      
        print "Total time for train with tree = %d"%(tEnd-tBeg)  
    else:
        Tr.TrainNGramFromTreeFiles     ()  
        tEnd = time.time()      
        print "Total time for train with tree = %d"%(tEnd-tBeg)  

class TrainConfig:
    def __init__(self, szConfigFile):
        cf=ConfigParser.ConfigParser()
        cf.read(szConfigFile)

        try:
            self.isParallel = cf.getboolean('global', 'PARALLEL')
        except:
            self.isParallel = DEFAULT_PARALLEL
            print 'PARALLEL not set, use defalt value ' + str(DEFAULT_PARALLEL)

        try:
            self.nBlockSize = cf.getint('global', 'BLOCK_SIZE')
        except:
            self.nBlockSize = DEFAULT_BLOCK_SIZE
            print 'BLOck SIZE not set use default value %d.'%(DEFAULT_BLOCK_SIZE)

        try:
            self.nLmVersion   = cf.getint('global', 'LM_VERSION')
        except:
            print 'LM_VERSION not set, use default value %d.'%(DEFAULT_LM_VERSION)
            self.nLmVersion   = DEFAULT_LM_VERSION

        try:
            self.nMaxMemForTreePrun = cf.get('global', 'MAX_MEM_FOR_TREE_PRUN')
        except:
            self.nMaxMemForTreePrun = DEFAULT_MAX_MEM_FOR_TREE_PRUN; 
            print 'MAX_MEM_FOR_TREE_PRUN not set use default value %s.'%(DEFAULT_MAX_MEM_FOR_TREE_PRUN)

        try:
            self.needCountTree = cf.getboolean('global', 'NEED_COUNT_TREE')
        except:
            self.needCountTree = DEFAULT_NEED_COUNT_TREE
            print 'NEED COUNT TREE not set, use default value ' + str(DEFAULT_NEED_COUNT_TREE)

        try:
            self.needMergeTree = cf.getboolean('global', 'NEED_MERGE_TREE')
        except:
            self.needMergeTree = DEFAULT_NEED_MERGE_TREE
            print 'NEED_MERGE_TREE not set, use default value ' + str(DEFAULT_NEED_MERGE_TREE)

        try:
            self.szCpsList = cf.get('global', 'CORPUS_LIST')
        except:
            raise ValueError, 'CORPUS LIST not set.'

        try:
            self.szPrunWordList = cf.get('global', 'PRUN_WORD_LIST')
        except:
            print 'PRUN WORD LIST not set.'
            self.szPrunWordList = ""

        try:
            self.szTreeDir = cf.get('global', 'TREE_DIR')
        except:
            raise ValueError, 'TREE DIR not set.'

        if self.szTreeDir[-1:] != '/':
            self.szTreeDir = self.szTreeDir + '/'

        self.szMergeDir = cf.get('global', 'MERGE_DIR')
        if self.szMergeDir[-1:] != '/':
            self.szMergeDir = self.szMergeDir + '/'

        try:
            self.szLexFile = cf.get('global', 'LEX_FILE')
        except:
            raise ValueError, 'LEX FILE not set.'

        try:
            self.nGramOrder = cf.getint('global', 'GRAM_ORDER')
            self.nRealOrder = self.nGramOrder
            if self.nGramOrder == 2 or self.nGramOrder == 1:
                self.nGramOrder = self.nGramOrder + 1
        except:
            self.nGramOrder = DEFAULT_GRAM_ORDER
            print 'GRAM ORDER not set, use default value %d.'%(DEFAULT_GRAM_ORDER)

        minCountArr  = DEFAULT_MIN_COUNT_ARR[:self.nRealOrder]
        try:
            szMinCount = cf.get('global', 'MIN_COUNT_ARR')
            szMinCountArr = szMinCount.split(',')
            for idx in range(self.nRealOrder):
                minCountArr[idx] = int(szMinCountArr[idx])
        except:
            print 'Min Count Array not set, use default value'
            print DEFAULT_MIN_COUNT_ARR

        self.szMinCountArr = ''
        for item in minCountArr:
            self.szMinCountArr += '%d '%item
        self.szMinCountArr = self.szMinCountArr[:-1]

        maxCountArr  = DEFAULT_MAX_COUNT_ARR[:self.nRealOrder]
        try:
            szMaxCount = cf.get('global', 'MAX_COUNT_ARR')
            szMaxCountArr = szMaxCount.split(',')
            for idx in range(self.nRealOrder):
                maxCountArr[idx] = int(szMaxCountArr[idx])
        except:
            print 'Max Count Array not set, use default value'
            print DEFAULT_MAX_COUNT_ARR

        self.szMaxCountArr = ''
        for item in maxCountArr:
            self.szMaxCountArr += '%d '%item
        self.szMaxCountArr = self.szMaxCountArr[:-1]

        try:
            self.szOutputKey = cf.get('global', 'OUTPUT_KEY')
        except:
            raise ValueError, 'OUTPUT_KEY not set.'

        self.szSmoothType = ''
        try:
            szSmoothArr       = cf.get('global', 'SMOOTH_TYPE')
            items             = szSmoothArr.split(',')
            while len(items) < self.nRealOrder:
                items.append(DEFAULT_SMOOTH_TYPE)
            items = items[:self.nRealOrder]
            for item in items:
                self.szSmoothType = self.szSmoothType + item + ' '
            self.szSmoothType = self.szSmoothType[:-1]
        except:
            for order in range(self.nRealOrder):
                self.szSmoothType = self.szSmoothType + DEFAULT_SMOOTH_TYPE + ' '
            #print 'SMOOTH_TYPE not set, use default value %s'%(DEFAULT_SMOOTH_TYPE)

        try:
            self.fWeightThreshold = cf.getfloat('global', 'WEIGHT_THRESHOLD')
        except:
            self.fWeightThreshold = DEFAULT_WEIGHT_THRESHOLD
            print 'WEIGHT_THRESHOLD not  set, use default value %f.'%(DEFAULT_WEIGHT_THRESHOLD)

        try:
            self.isTxtHasWeight   = cf.getboolean('global', 'TEXT_HAS_WEIGHT')
        except:
            self.isTxtHasWeight   = DEFAULT_TXT_HAS_WEIGHT
            print 'TXT_HAS_WEIGHT not set, use default value ' + str(DEFAULT_TXT_HAS_WEIGHT)

        if self.isParallel:
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
        print 'IS_PARALLEL     : ' + str(self.isParallel) + '.'
        print 'BLOCK_SIZE     : %d.'%(self.nBlockSize)
        print 'MAX_MEM_FOR_TREE_PRUN     : %s.'%(self.nMaxMemForTreePrun)
        print 'NEED_COUNT_TREE  : ' + str(self.needCountTree) + '.'
        print 'NEED_MERGE_TREE  : ' + str(self.needMergeTree) + '.'
        print 'CORPUS_LIST      : %s.'%(self.szCpsList)
        print 'TREE_DIR       : %s.'%(self.szTreeDir)
        print 'LEX_FILE       : %s.'%(self.szLexFile)
        print 'OUTPUT_KEY     : %s.'%(self.szOutputKey)
        print 'GRAM_ORDER     : %d.'%(self.nGramOrder)
        print 'REAL_ORDER     : %d.'%(self.nRealOrder)
        print 'MIN_COUNT_ARR  : %s.'%(self.szMinCountArr)
        print 'MAX_COUNT_ARR  : %s.'%(self.szMaxCountArr)
        print 'SMOOTH_TYPE    : %s.'%(self.szSmoothType)
        print 'WEIGHT_THRESHOLD : %e.'%(self.fWeightThreshold)
        print 'TEXT_HAS_WEIGHT  : ' + str(self.isTxtHasWeight) + '.'
        if self.isParallel:
            print 'CPU_NUM          : %d'%(self.m_nCpuNum)
            print 'ppservers        : '
            print self.m_Servers
        print '----------------config end--------------------'

#===============================================================================           
if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise AttributeError, 'usage: python ppTrainLM.py config'

    config = TrainConfig(sys.argv[1])
    config.PrintConfig()

    if config.nLmVersion == 1 and config.nGramOrder <= 3:
        raise AttributeError, 'not support GramOrder less than 3 using Version1, you can use Version0 instead.'

    if config.isParallel:
        if config.needCountTree:
            tBeg = time.time()
            CorpusToTreeParallel (config)
            tCountTree = time.time()-tBeg

        if config.needMergeTree or config.needCountTree:
            tBeg = time.time()
            MergeTreeParallel(config)
            tMergeTree = time.time()-tBeg
            
        tBeg = time.time()
        TrainWithTree(config)
        tEnd = time.time()
        tTrainWithTree = tEnd - tBeg

        print '--------------------------------------------'
        if config.needCountTree:
            print 'Count Tree : %d s'%(tCountTree)
        if config.needCountTree or config.needMergeTree:
            print 'Merge Tree : %d s'%(tMergeTree)
        print "Total time for train with tree = %d"%(tTrainWithTree)
    else:    
        TrainSeq(config)

