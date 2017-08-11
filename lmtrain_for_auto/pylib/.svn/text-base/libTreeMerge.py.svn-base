#---------------------------------------------------------------
# Module: 	libCorpusCell.py
# Function: Perfrom corpus processing and indexing
# Authoer:  Jialei
# Date:	 	Nov.16, 2010
#---------------------------------------------------------------
import sys, os, time, types, copy, string, inspect, Queue, thread, logging
import threading
#import pickle
import myPickle as pickle
import pp
from ppLMToolKit import *

#-----------------------------------
# function: gf_SendCmptCell
#-----------------------------------
def gf_Map (Memfile):                        #map operation   
    return 0
    if not isinstance(Memfile, types.StringType):
        key = Memfile.cAttri.CalKey()
    else:
        curFile    = MemFile()
        curFile.Init (Memfile, len(Memfile), 0)
        key = curFile.cAttri.CalKey()
    return key

def gf_SendCmptCell ():                      #state each cmpt cell in each worker
    CmptCell =  MemFile()   
    globals().update(locals())     
    #retStr = CmptCell.SelfTest()
    return 0

def gf_SetEachCmptCell(Memfile1, Memfile2, nMaxMemForTreePrun):  #reduce operation
    ret = CmptCell.merge(Memfile1, Memfile2, nMaxMemForTreePrun)

    #merge error, return empty string
    if ret != 0:
        print 'merge tree failed.'
        CmptCell.clear()
        return ''
    strRet = str(CmptCell)
    print 'result length %d.'%(len(strRet))
    CmptCell.clear()
    return  strRet

"""
def gf_Map (str):                            #map operation    
    return 0

def gf_SendCmptCell ():                      #state each cmpt cell in each worker
    retStr = "This is used in debugger for string cancatenation!"
    return retStr

def gf_SetEachCmptCell(str1, str2):          #reduce operation 
    time.sleep(0.01)
    strRes = "%s%s%s"%(str1, ',',  str2)
    return  strRes
"""

g_modules=('time', 'string', 'ppLMToolKit*')

#------------------------------------------
#     Operation
#------------------------------------------
class Operation:
             
    """The below two functions should be
       over write from outside """            
     
    def __init__(self):
        self.sfuncReduce  = None
        self.sargsReduce  = None        
        self.sfuncMap     = None
        self.sargsMap     = None
        self.__sfuncHM    = {}
        self.__sourcesHM  = {}

    def InitMap(self, func, args=(), depfuncs=(), modules=()):
        (self.sfuncMap, self.sargsMap) = self.getPickledFun (func, args, depfuncs, modules)     
          
    def InitReduce(self, func, args=(), depfuncs=(), modules=()):             
        (self.sfuncReduce, self.sargsReduce) = self.getPickledFun (func, args, depfuncs, modules)
                               
    def getPickledFun(self, func, args=(), depfuncs=(), modules=()):   
        if isinstance(func, types.MethodType) and func.im_self is not None:
            args = (func.im_self, ) + args
        # if there is an instance of a user deined class in the arguments add whole class to dependancies
        for arg in args:
            if isinstance(arg, types.InstanceType) or str(type(arg))[:6] == "<class": 
                #Checks for both classic or new class instances                            
                if ppcommon.is_not_imported(arg, modules):     # do not include source for imported modules
                    depfuncs += tuple(ppcommon.get_class_hierarchy(arg.__class__))
        # if there is a function in the arguments add this function to dependancies
        for arg in args:
            if isinstance(arg, types.FunctionType):
                depfuncs += (arg, )

        # function format
        sfunc = self.__dumpsfunc( (func, ) + depfuncs, modules )        
        sargs = pickle.dumps(args, 1)
                                       
        return (sfunc, sargs)

    def __get_source(self, func):
        """Fetches source of the function"""
        hashf = hash(func)
        if hashf not in self.__sourcesHM:
            #get lines of the source and adjust indent
            sourcelines = inspect.getsourcelines(func)[0]
            #remove indentation from the first line
            sourcelines[0] = sourcelines[0].lstrip()
            self.__sourcesHM[hashf] = "".join(sourcelines)
        return self.__sourcesHM[hashf]
        
    def __dumpsfunc(self, funcs, modules):
        """Serializes functions and modules"""
        hashs = hash(funcs + modules)
        if hashs not in self.__sfuncHM:
            sources = [self.__get_source(func) for func in funcs]
            self.__sfuncHM[hashs] = pickle.dumps(
                    (funcs[0].func_name, sources, modules),1)
        return self.__sfuncHM[hashs]

#------------------------------------------
#     CMapReduce
#------------------------------------------                                             
class CMapReduce:

    def __init__( self, nMaxMemForTreePrun, ncpus="autodetect", loglevel=logging.WARN, logstream=sys.stderr,
            pickle_proto=1):
        """Initialization of the thread management"""
        
        self.__selfLoopRes      = Queue.Queue()
        self.nMaxMemForTreePrun = nMaxMemForTreePrun
                
        self.inputDict          = {} 
        self.__lock_inputDict   = threading.Lock()
        
        #function preprocess for server comutation
        self.op                 = Operation() 
        
        #localhost server initialization ( start each compt cell in workers of server)      
        self.m_jobs               = []
        self.m_ppJobServer      = pp.Server(ncpus=ncpus, ppservers=())
        nWorkerNum              = self.m_ppJobServer.get_worker_num()        
        for wId in range(nWorkerNum):              
            self.m_ppJobServer.submitToQueue(gf_SendCmptCell, args=(), modules=g_modules)   
        (self.m_jobs, jobNum) = self.m_ppJobServer.BatchDoJob()    
        print "Total compute cell number = %d"%(len(self.m_jobs))          
        for job in self.m_jobs:  
            job()
            job.printLog()
        self.m_jobs = []  
                
        # logger initializtaion

    def __import_module(self, name):
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod
           
    def __preprocess(self, sourceCodes):
        fname, fsources, imports = pickle.loads(sourceCodes)
        fobjs = []
        #Load function object
        for fsource in fsources:
            if fsource == "":    continue
            fobjs.append(compile(fsource, '<string>', 'exec'))
        #Import module
        for module in imports:     
            if module[len(module)-1] == '*':
                module = module[0:len(module)-1]
                try:
                    exec('from %s import *'%(module))     
                    #self.__dict__.update(locals())
                    globals().update(locals())
                except:
                    print "An error has occured during the module import1"
            else:
                try:
                    #self.__dict__[module.split('.')[0]] = self.__import_module(module)
                    globals()[module.split('.')[0]] = self.__import_module(module)
                except:
                    print "An error has occured during the module import2"
            try:
                module = '_' + module
                #self.__dict__[module.split('.')[0]] = __import__(module) 
                globals()[module.split('.')[0]] = self.__import_module(module)  
            except:
                pass     
        return fname, fobjs
    
    def setMapfun (self, funs, sargs):
        fname, fobjs = self.__preprocess (funs)                                          
        for fobj in fobjs:
            try:
                exec(fobj)
                self.__dict__.update(locals())
            except:
                print "An error has occured during the " + "function import"                                  
        self.Map_args = pickle.loads(sargs)                 
        self.Map_fun  = locals()[fname] 
        
    def Map(self, inputArgs):
        try:
            Map_args = self.Map_args + (inputArgs,) # pre-setting parameter + current parameter
            retValue = self.Map_fun( *Map_args )
            return retValue
        except:
            print "An error has occured during the map execution"
            return None      

    def getRawMapReduceRes(self, sout=""):    
        """ Returned value is a string. string format is defined in cMapRdsSubmitRes."""  
                           
        #If there's left task unfinished, implement all the lest task 
        self.__lock_inputDict.acquire()          
        for key in self.inputDict.keys():
            if len(self.inputDict[key]) > 1 or self.__selfLoopRes.qsize() != 0: #Reduce needs at least two files
                self.__lock_inputDict.release()
                self.__recursiveReduce()
            else:
                self.__lock_inputDict.release()
                
        # clear input of dict and nJobNum                                       
        resDict        = copy.copy(self.inputDict)
        self.inputDict = {}                  
        self.nJobNum   = 0
        
        # take result from resDict
        keys   = []
        result = []
        for key in resDict.keys():
            keys.append  ( key )
            result.append(resDict[key][0] )  #After reduce, only one value is left for each key

        # return the original results
        return [keys, result]

    def __submitJob(self, *args):       
        
        #perfrom reduce operation in server
        self.op.InitReduce(gf_SetEachCmptCell, args=(args[0], args[1], args[2])) 
        job = self.m_ppJobServer.insert (self.op.sfuncReduce, self.op.sargsReduce)    
        self.__selfLoopRes.put(job)                        
    
    def __recursiveReduce(self):
        """Perform reduce by all the working threads recursively"""
        while(1):
            self.__lock_inputDict.acquire() 
            #if dict input size is above 1, submit job          
            for key in self.inputDict.keys():
                if len(self.inputDict[key]) > 1: #Reduce needs at least two files
                    break;
            else: 
                if self.__selfLoopRes.qsize() > 0:
                    #Get result of the previous submission        
                    while self.__selfLoopRes.qsize() > 0 :
                        job = self.__selfLoopRes.get()
                        input = job()
                        job.printLog()
                        key =  self.Map(input)

                        #merge error, return empty string
                        if input == "":
                            print 'merge tree failed.'
                            self.inputDict[key] = []
                            break

                        if not self.inputDict.has_key(key):
                            self.inputDict[key] = [input] 
                        else:
                            self.inputDict[key].append(input)
                    self.__lock_inputDict.release() 
                    continue                
                else:
                    self.__lock_inputDict.release()                
                    return

            #submit job to threads and threads will do reduce
            for id in xrange( len(self.inputDict[key]) / 2 ):
                input1 = self.inputDict[key].pop(0)
                input2 = self.inputDict[key].pop(0)
                self.__submitJob (str(input1), str(input2), self.nMaxMemForTreePrun)             
            self.__lock_inputDict.release()      
        
    #---------------------------------------------------
    # Only submit job to local server and no implement
    #-------------------------------------------------- 
    def doLocal(self):
        self.__recursiveReduce() 
        
    def submitLocal (self, inputList=None ):
        """The function is used by local client. All jobs are sumbited in batch mode. 
        Only one result is obtained by call getMapReduceRes()"""
      
        self.__lock_inputDict.acquire()    
        
        if not isinstance(inputList, types.ListType):
            inputList = [inputList]
            
        #Insert each item into inputDict
        logging.debug("pplocalhost submitLocal with input: %s", inputList[0])                                               
        for item in inputList:         
            key =  self.Map(item)
            if not self.inputDict.has_key(key):
                self.inputDict[key] = [item]     #Before reduce, each key has multiple values
            else:
                self.inputDict[key].append(item)   

        #perform reduce   
        for key in self.inputDict.keys():
            if len(self.inputDict[key]) > 1: #Reduce needs at least two files
                for id in xrange( len(self.inputDict[key]) / 2 ):
                    input1 = self.inputDict[key].pop(0)
                    input2 = self.inputDict[key].pop(0)
                    #submit job to threads and threads will do reduce
                    self.__submitJob (str(input1), str(input2), self.nMaxMemForTreePrun)
                                                           
        self.__lock_inputDict.release()
        #recursive reduce
        #thread.start_new_thread(self.doLocal, ())
        return
                                                                                                                                                                                                                                                             
#-----------------------------------
# function: ppTreeMerge
#-----------------------------------    
class ppTreeMerge:

    def __init__(self, nCpuNum, nMaxMemForTreePrun):
        #init thread number
        try: self.m_nThreadNum    = nCpuNum
        except: self.m_nThreadNum = "autodetect"

        self.nMaxMemForTreePrun = nMaxMemForTreePrun
        
        #operation initialization
        self.op = Operation () 
        self.op.InitMap (gf_Map, args=(), depfuncs=(), modules=g_modules )
        
        #parallel map-reduce class
        self.mapReduce = CMapReduce (nMaxMemForTreePrun, ncpus = self.m_nThreadNum)
        self.mapReduce.setMapfun (self.op.sfuncMap, self.op.sargsMap) 
                                      
    def pp_submit (self, item):   
        # submit each merged result one by one 
        self.mapReduce.submitLocal (item)
        return 
        
    def pp_doJobs (self):
        self.mapReduce.doLocal()
                         
    def GetPPresult (self):   
        # return format is [ [keys list], [Merged results list ] ]. 
        return self.mapReduce.getRawMapReduceRes()  

#-------------------------------------------------------------------
#               main test function
#-------------------------------------------------------------------
       
if __name__ == '__main__':   

    mergeClass = ppTreeMerge(config)
    t1 = time.time()

    for ii in xrange(2000): 
        mergeClass.pp_submit (ii)   
    res = mergeClass.GetPPresult()
     #
    values= res[1][0].split(',')
    t2 = time.time()
    print "Implement time = %d"%(t2-t1)
    #values.sort()
    #print values
    
