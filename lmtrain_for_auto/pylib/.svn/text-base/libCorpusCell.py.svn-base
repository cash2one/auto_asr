#---------------------------------------------------------------
# Module: 	libCorpusCell.py
# Function: Perfrom corpus processing and indexing
# Authoer:  Jialei
# Date:	 	Nov.16, 2010
#---------------------------------------------------------------
import os, sys, time, thread, logging, types
import pp
from ppLMToolKit import *
#-----------------------------------
# function: gf_SendCmptCell
#-----------------------------------
def gf_SendCmptCell (szLexFl, szCorpusFl, text_has_weights):         
    #print "Begin compute cell establish"
    try:
        del CorpusCmpt
    except:
        pass

    CorpusCmpt = LMCountCell()
    if text_has_weights:
        ret = CorpusCmpt.__setstate_SenWt__(szLexFl, szCorpusFl)
        if ret != 0:
            print 'SetState SentWeight failed.'
            return -1
    else:
        ret = CorpusCmpt.__setstate__(szLexFl, szCorpusFl)
        if ret != 0:
            print 'SetState failed.'
            return -1
    globals().update(locals())    

    print CorpusCmpt.SelfTest()
    return 0

#-----------------------------------
# function: gf_GetEachCmptCellRes
#-----------------------------------
def gf_GetEachCmptCellRes(wordIdSt, wordIdEd, nCurGram, text_has_weights, szCorpusFl):
    if text_has_weights:
        strRet = CorpusCmpt.GetCellPyOutput_SenWt(wordIdSt, wordIdEd, nCurGram)
    else:
        strRet = CorpusCmpt.GetCellPyOutput(wordIdSt, wordIdEd, nCurGram)
    return strRet
    
#-----------------------------------
# function: CorpusCell
#-----------------------------------    
class CorpusCell:
    def __init__(self, ppservers, ncpus, txtHasWeight, m_LexFile):
        self.text_has_weights = txtHasWeight
        self.job_server       = pp.Server(ncpus, ppservers, jobInsertType=2)
        self.jobs             = []
        self.m_nPrsCps        = 0
        self.m_LexFile        = m_LexFile
        self.m_CorpusList     = []
        
    def pp_GetStatus(self):
        self.job_server.print_stats()        
        
    #submit count task for every job_server.
    def SubmitCntTask(self, corpusList):
        #The below wait is must needed for localhost test
        time.sleep(0.001)

        jobNum = 0
        nWorkerNum = self.job_server.get_worker_num()  
        self.m_nPrsCps = nWorkerNum
        if self.m_nPrsCps > len(corpusList):
            self.m_nPrsCps = len(corpusList)

        self.m_CorpusList = corpusList
        self.jobs = []
        for wId in range(self.m_nPrsCps):
            self.job_server.submitToQueue(gf_SendCmptCell,
                        args=(self.m_LexFile, corpusList[wId], self.text_has_weights), 
                        modules=("time","ppLMToolKit", "ppLMToolKit*" ))                 
            time.sleep(0.001)

        (self.jobs, jobNum) = self.job_server.BatchDoJob()

        print "Total compute cell number = %d"%(len(self.jobs))          
        for job in self.jobs:  
            ret = job()
            job.printLog()
            if ret != 0:
                print 'Get Count result failed.'
                return -1
        self.jobs = []
        return self.m_nPrsCps
                               
    #submit task to extract gram tree for every task_server
    def SubmitObtTreeTask(self, wordIdSt, wordIdEd, nCurGram):
        for wid in range(self.m_nPrsCps):
            self.job_server.submitToQueue(gf_GetEachCmptCellRes, 
                        args=(wordIdSt, wordIdEd, nCurGram, self.text_has_weights, self.m_CorpusList[wid]),
                        modules=("time","ppLMToolKit", "ppLMToolKit*" ))                 
            time.sleep(0.001)

        (self.jobs, jobNum) = self.job_server.BatchDoJob()                   

        resList = []
        for job in self.jobs:
            result = job()
            if result == None:
                print 'Get Gram Tree failed.'
                return None
            resList.append(result)
        self.jobs = []
        return resList
