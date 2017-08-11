# Parallel Python Software: http://www.parallelpython.com
# Copyright (c) 2005-2009, Vitalii Vanovschi
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the author nor the names of its contributors
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
"""
Parallel Python Software, PP Worker

http://www.parallelpython.com - updates, documentation, examples and support
forums
"""
import sys
import os
import StringIO
#import cPickle as pickle
import myPickle as pickle
import pptransport

copyright = "Copyright (c) 2005-2009 Vitalii Vanovschi. All rights reserved"
version = "1.5.7"

#------------------------------------------
# Name: import_module 
#------------------------------------------
def import_module(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod
    
#------------------------------------------
# Name: preprocess 
# Function: 1. Load function object
#           2. import module
#------------------------------------------

def preprocess(msg):
    fname, fsources, imports = pickle.loads(msg)
    fobjs = []
    #1. Load function object
    for fsource in fsources:
        if fsource == "":    continue
        fobjs.append(compile(fsource, '<string>', 'exec'))
    #2. Import module
    for module in imports:     
        if module[len(module)-1] == '*':
            module = module[0:len(module)-1]
            try:
                #print ("Begin: from %s import *:"%(module))
                exec('from %s import *'%(module))
                #print ("  End: from %s import *:"%(module))                
                globals().update(locals())

            except:
                print "An error has occured during the module import"
                sys.excepthook(*sys.exc_info()) 
        else:
            try:
                #print ("Load modules:%s"%module)
                globals()[module.split('.')[0]] = __import__(module)

            except:
                print "An error has occured during the module import"
                sys.excepthook(*sys.exc_info())
        try:
            module = '_' + module
            globals()[module.split('.')[0]] = __import__(module)   
        except:
            pass  
    return fname, fobjs

"""
def preprocess(msg):
    fname, fsources, imports = pickle.loads(msg)
    fobjs = [compile(fsource, '<string>', 'exec') for fsource in fsources]
    for module in imports:
        try:
            globals()[module.split('.')[0]] = __import__(module)
        except:
            print "An error has occured during the module import"
            sys.excepthook(*sys.exc_info())
    return fname, fobjs
"""

def writeDebug(strContent):
    debug = open("./ppworker.debug","a+")
    debug.write(strContent)
    debug.close()

class _WorkerProcess(object):

    def __init__(self):
        self.hashmap = {}
        self.e = sys.__stderr__
        self.sout = StringIO.StringIO()
        sys.stdout = self.sout
        sys.stderr = self.sout
        self.t = pptransport.CPipeTransport(sys.stdin, sys.__stdout__)
        self.t.send(str(os.getpid()))
        self.pickle_proto = int(self.t.receive())        
        
    def run(self):
        try:
            #execution cycle
            while 1:             
                
                __fname, __fobjs = self.t.creceive(preprocess)
                           
                __sargs = self.t.receive()

                for __fobj in __fobjs:
                    try:
                        exec(__fobj)
                        globals().update(locals())
                    except:
                        print "An error has occured during the " + \
                              "function import"
                        sys.excepthook(*sys.exc_info())
                                  
                __args = pickle.loads(__sargs)

                                      
                __f = locals()[__fname]
                try:
                    __result = __f(*__args)
                except:
                    print "An error has occured during the function execution"
                    sys.excepthook(*sys.exc_info())
                    __result = None                    

                                        
                # change part: don't pickle the __result any more
                # Choice 1: For the trustable internet transmission and easy debug 
                __sresult = pickle.dumps((__result, self.sout.getvalue()), self.pickle_proto)
                # Choice 2: For the fast speed and don't do pickle any more. The __result must be a string             
                #__sresult = str(__result)
                # end change   

                # for debug
                #writeDebug("\t __result = %s\n"%(__result))
                #end debug
                                
                self.t.send(__sresult)
                self.sout.truncate(0) 
        except:
            print "Fatal error has occured during the function execution"
            sys.excepthook(*sys.exc_info())
            __result = None
            # Choice 1: For the trustable internet transmission and easy debug 
            __sresult = pickle.dumps((__result, self.sout.getvalue()), self.pickle_proto)
            # Choice 2: For the fast speed and don't do pickle any more. The __result must be a string             
            #__sresult = None
            self.t.send(__sresult)


if __name__ == "__main__":
        # add the directory with ppworker.py to the path
        sys.path.append(os.path.dirname(__file__))
        wp = _WorkerProcess()
        wp.run()

# Parallel Python Software: http://www.parallelpython.com
