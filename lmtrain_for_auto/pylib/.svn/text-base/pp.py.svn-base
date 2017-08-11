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
Parallel Python Software, Execution Server

http://www.parallelpython.com - updates, documentation, examples and support
forums
"""

import os
import thread
import logging
import inspect
import sys
import types
import time
import atexit
import user
#import cPickle as pickle
import myPickle as pickle
import pptransport
import ppauto
import threading
import ppcommon

copyright = "Copyright (c) 2005-2009 Vitalii Vanovschi. All rights reserved"
version = "1.5.7"

# reconnect persistent rworkers in 5 sec
_RECONNECT_WAIT_TIME = 5

# we need to have set even in Python 2.3
try:
    set
except NameError:
    from sets import Set as set 

_USE_SUBPROCESS = False
try:
    import subprocess
    _USE_SUBPROCESS = True
except ImportError:
    import popen2


class _Task(object):
    """Class describing single task (job)
    """

    def __init__(self, server, tid, callback=None,
            callbackargs=(), group='default'):
        """Initializes the task"""
        self.lock = thread.allocate_lock()
        self.lock.acquire()
        self.sout = ''
        self.tid = tid
        self.server = server
        self.callback = callback
        self.callbackargs = callbackargs
        self.group = group
        self.finished = False
        self.unpickled = False

    def finalize(self, sresult):
        """Finalizes the task.
           For internal use only"""
        self.sresult = sresult
        if self.callback:
            self.__unpickle()
        self.lock.release()
        self.finished = True

    def __call__(self, raw_result=False):
        """Retrieves result of the task"""
        self.wait()

        if not self.unpickled and not raw_result:
            self.__unpickle()

        if raw_result:
            return self.sresult
        else:
            return self.result

    def wait(self):
        """Waits for the task"""
        if not self.finished:
            self.lock.acquire()
            self.lock.release()


    def __unpickle(self):
        """Unpickles the result of the task"""
        #Begin change         
        #choice one:  For the fast speed and don't do pickle any more in ppworker.py
        #self.result = str(self.sresult) 
        #choice two:  For the nice internet environment and easy debug
        if self.sresult == None:
            self.result = None
            self.sout = ''
            return

        # change part: don't pickle the __result any more
        # Choice 1: For the trustable internet transmission and easy debug 
        self.result, self.sout = pickle.loads(self.sresult)
        # Choice 2: For the fast speed and don't do pickle any more. The __result must be a string             
        # self.result = str(self.sresult)
        # self.sout    = ''
        # end change   

        self.unpickled = True          
        if self.callback:
            args = self.callbackargs + (self.result, )
            self.callback(*args)

    def printLog(self, logstream=sys.stdout):
        if not logstream:
            logstream = open("./worker%d.log"%(self.tid),"wt")
        self.lock.acquire()
        logstream.write( "\n********taskId print begin= %d***********\n"%(self.tid) )
        logstream.write(self.sout)
        #logstream.write(str(self.result))
        logstream.write("\n")        
        logstream.write( "********taskId print end  = %d***********\n"%(self.tid) )    
        self.lock.release()   
        
class _Worker(object):
    """Local worker class
    """
    command = [sys.executable, "-u",
            os.path.dirname(os.path.abspath(__file__))
            + os.sep + "ppworker.py"]

    command.append("2>/dev/null")

    def __init__(self, restart_on_free, pickle_proto):
        """Initializes local worker"""
        self.restart_on_free = restart_on_free
        self.pickle_proto = pickle_proto
        self.start()

    def start(self):
        """Starts local worker"""
        if _USE_SUBPROCESS:
            proc = subprocess.Popen(self.command, stdin=subprocess.PIPE, \
                    stdout=subprocess.PIPE, stderr=None, \
                    shell=False)
            self.t = pptransport.CPipeTransport(proc.stdout, proc.stdin)
        else:
            self.t = pptransport.CPipeTransport(\
                    *popen2.popen3(self.command)[:2])

        self.pid = int(self.t.receive())
        self.t.send(str(self.pickle_proto))
        self.is_free = True
        self.HaveUsed = False

    def stop(self):
        """Stops local worker"""
        self.is_free = False
        self.t.send('EXIT') # can send any string - it will exit
        self.t.close()

    def restart(self):
        """Restarts local worker"""
        self.stop()
        self.start()

    def free(self):
        """Frees local worker"""
        if self.restart_on_free:
            self.restart()
        else:
            self.is_free = True


class _RWorker(pptransport.CSocketTransport):
    """Remote worker class
    """

    def __init__(self, host, port, secret, message=None, persistent=True):
        """Initializes remote worker"""
        self.persistent = persistent
        self.host = host
        self.port = port
        self.secret = secret
        self.address = (host, port)
        self.id = host + ":" + str(port)
        self.message = message
        logging.debug("Creating Rworker id=%s persistent=%s"
                % (self.id, persistent))
        self.connect(self.message)
        self.is_free = True
        self.HaveUsed = False

    def __del__(self):
        """Closes connection with remote server"""
        self.close()

    def connect(self, message=None):
        """Connects to a remote server"""
        while True:
            try:
                pptransport.SocketTransport.__init__(self)
                self._connect(self.host, self.port)
                if not self.authenticate(self.secret):
                    logging.error("Authentication failed for host=%s, port=%s"
                            % (self.host, self.port))
                    return False
                if message:
                    self.send(message)
                self.is_free = True
                return True
            except:
                if not self.persistent:
                    logging.debug("Deleting from queue Rworker %s"
                            % (self.id, ))
                    return False
#                print sys.excepthook(*sys.exc_info())
                logging.debug("Failed to reconnect with " \
                        "(host=%s, port=%i), will try again in %i s"
                        % (self.host, self.port, _RECONNECT_WAIT_TIME))
                time.sleep(_RECONNECT_WAIT_TIME)


class _Statistics(object):
    """Class to hold execution statisitcs for a single node
    """

    def __init__(self, ncpus, rworker=None):
        """Initializes statistics for a node"""
        self.ncpus = ncpus
        self.time = 0.0
        self.njobs = 0
        self.rworker = rworker


class Template(object):
    """Template class
    """

    def __init__(self, job_server, func, depfuncs=(), modules=(),
            callback=None, callbackargs=(), group='default', globals=None):
        """Creates Template instance

           jobs_server - pp server for submitting jobs
           func - function to be executed
           depfuncs - tuple with functions which might be called from 'func'
           modules - tuple with module names to import
           callback - callback function which will be called with argument
                   list equal to callbackargs+(result,)
                   as soon as calculation is done
           callbackargs - additional arguments for callback function
           group - job group, is used when wait(group) is called to wait for
           jobs in a given group to finish
           globals - dictionary from which all modules, functions and classes
           will be imported, for instance: globals=globals()"""
        self.job_server = job_server
        self.func = func
        self.depfuncs = depfuncs
        self.modules = modules
        self.callback = callback
        self.callbackargs = callbackargs
        self.group = group
        self.globals = globals

    def submit(self, *args):
        """Submits function with *arg arguments to the execution queue
        """
        return self.job_server.submit(self.func, args, self.depfuncs,
                self.modules, self.callback, self.callbackargs,
                self.group, self.globals)


class Server(object):
    """Parallel Python SMP execution server class
    """

    default_port = 60000
    default_secret = "epo20pdosl;dksldkmm"

    def __init__(self, ncpus="autodetect", ppservers=(), secret=None,
            loglevel=logging.WARN, logstream=sys.stderr,
            restart=False, proto=1, jobInsertType=1):
        """Creates Server instance

           ncpus - the number of worker processes to start on the local
                   computer, if parameter is omitted it will be set to
                   the number of processors in the system
           ppservers - list of active parallel python execution servers
                   to connect with
           secret - passphrase for network connections, if omitted a default
                   passphrase will be used. It's highly recommended to use a
                   custom passphrase for all network connections.
           loglevel - logging level
           logstream - log stream destination
           restart - wheather to restart worker process after each task completion
           proto - protocol number for pickle module

           With ncpus = 1 all tasks are executed consequently
           For the best performance either use the default "autodetect" value
           or set ncpus to the total number of processors in the system
        """

        if not isinstance(ppservers, tuple):
            raise TypeError("ppservers argument must be a tuple")

        self.__initlog(loglevel, logstream)
        logging.debug("Creating server instance (pp-" + version+")")
        self.__tid = 0
        self.__active_localtask_Num = 0
        self.__active_task_lock     = thread.allocate_lock()
        self.__queue = []
        self.__queue_lock = thread.allocate_lock()
        self.__workers = []
        self.__rworkers = []
        self.__rworkers_reserved = []
        self.__rworkers_reserved4 = []
        self.__rworkers_reset     = []
        self.__sourcesHM = {}
        self.__sfuncHM = {}
        self.__waittasks = []
        self.__waittasks_lock = thread.allocate_lock()
        self._exiting = False
        self.__accurate_stats = True
        self.autopp_list = {}
        self.__active_rworkers_list_lock = thread.allocate_lock()
        self.__restart_on_free = restart
        self.__pickle_proto = proto
        # To allow control for the batch implement mode 
        self.__ServerEvent = threading.Event()
        # To prevent starting too much threads(> 300) becasue the iteratve call of schedule() 
        self.__IterNum_lock = thread.allocate_lock()
        self.__IterNum = 0
        # To record the active tasks for time coordination
        self.__active_tasks  = []

        # add local directory and sys.path to PYTHONPATH
        pythondirs = [os.getcwd()] + sys.path

        if "PYTHONPATH" in os.environ and os.environ["PYTHONPATH"]:
            pythondirs += os.environ["PYTHONPATH"].split(os.pathsep)
        os.environ["PYTHONPATH"] = os.pathsep.join(set(pythondirs))

        atexit.register(self.destroy)
        self.__stats = {"local": _Statistics(0)}
        self.set_ncpus(ncpus)

        self.ppservers = []
        self.auto_ppservers = []

        for ppserver in ppservers:
            ppserver = ppserver.split(":")
            host = ppserver[0]
            if len(ppserver)>1:
                port = int(ppserver[1])
            else:
                port = Server.default_port
            if host.find("*") == -1:
                self.ppservers.append((host, port))
            else:
                if host == "*":
                    host = "*.*.*.*"
                interface = host.replace("*", "0")
                broadcast = host.replace("*", "255")
                self.auto_ppservers.append(((interface, port),
                        (broadcast, port)))
        self.__stats_lock = thread.allocate_lock()
        if secret is not None:
            if not isinstance(secret, types.StringType):
                raise TypeError("secret must be of a string type")
            self.secret = str(secret)
        elif hasattr(user, "pp_secret"):
            secret = getattr(user, "pp_secret")  
            if not isinstance(secret, types.StringType):
                raise TypeError("secret must be of a string type")
            self.secret = str(secret)
        else:
            self.secret = Server.default_secret
        self.__connect(jobInsertType)
        self.__creation_time = time.time()
        time.sleep(1)
        self.sortRWorker()
        logging.info("pp local server started with %d workers"
                % (self.__ncpus, ))

    def submit(self, func, args=(), depfuncs=(), modules=(),
            callback=None, callbackargs=(), group='default', globals=None):
        """Submits function to the execution queue

            func - function to be executed
            args - tuple with arguments of the 'func'
            depfuncs - tuple with functions which might be called from 'func'
            modules - tuple with module names to import
            callback - callback function which will be called with argument
                    list equal to callbackargs+(result,)
                    as soon as calculation is done
            callbackargs - additional arguments for callback function
            group - job group, is used when wait(group) is called to wait for
            jobs in a given group to finish
            globals - dictionary from which all modules, functions and classes
            will be imported, for instance: globals=globals()
        """

        # perform some checks for frequent mistakes
        if self._exiting:
            raise RuntimeError("Cannot submit jobs: server"\
                    " instance has been destroyed")

        if not isinstance(args, tuple):
            raise TypeError("args argument must be a tuple")

        if not isinstance(depfuncs, tuple):
            raise TypeError("depfuncs argument must be a tuple")

        if not isinstance(modules, tuple):
            raise TypeError("modules argument must be a tuple")

        if not isinstance(callbackargs, tuple):
            raise TypeError("callbackargs argument must be a tuple")

        for module in modules:
            if not isinstance(module, types.StringType):
                raise TypeError("modules argument must be a list of strings")

        tid = self.__gentid()
        if globals:
            modules += tuple(self.__find_modules("", globals))
            modules = tuple(set(modules))
            self.__logger.debug("Task %i will autoimport next modules: %s" %
                    (tid, str(modules)))
            for object1 in globals.values():
                if isinstance(object1, types.FunctionType) \
                        or isinstance(object1, types.ClassType):
                    depfuncs += (object1, )

        task = _Task(self, tid, callback, callbackargs, group)

        self.__waittasks_lock.acquire()
        self.__waittasks.append(task)
        self.__waittasks_lock.release()

        # if the function is a method of a class add self to the arguments list
        if isinstance(func, types.MethodType) and func.im_self is not None:
            args = (func.im_self, ) + args

        # if there is an instance of a user deined class in the arguments add
        # whole class to dependancies
        for arg in args:
            # Checks for both classic or new class instances
            if isinstance(arg, types.InstanceType) \
                    or str(type(arg))[:6] == "<class":
                # do not include source for imported modules
                if ppcommon.is_not_imported(arg, modules):
                    depfuncs += tuple(ppcommon.get_class_hierarchy(arg.__class__))

        # if there is a function in the arguments add this
        # function to dependancies
        for arg in args:
            if isinstance(arg, types.FunctionType):
                depfuncs += (arg, )

        sfunc = self.__dumpsfunc((func, ) + depfuncs, modules)
        sargs = pickle.dumps(args, self.__pickle_proto)

        self.__queue_lock.acquire()
        self.__queue.append((task, sfunc, sargs))
        self.__queue_lock.release()

        self.__logger.debug("Task %i submited, function='%s'" %
                (tid, func.func_name))                          
        self.__scheduler()
        return task

    def wait(self, group=None):
        # Waits for all jobs in a given group to finish.
        # If group is omitted waits for all jobs to finish        
        while True:
            self.__waittasks_lock.acquire()
            for task in self.__waittasks:
                if not group or task.group == group:
                    self.__waittasks_lock.release()
                    task.wait()
                    break
            else:
                self.__waittasks_lock.release()
                break 
                                       
    def waitAliveTask(self):
        """ Waits untill all active jobs are finish."""  
           
        #self.__logger.debug("Wait untill active tasks are all finished") 
        while True:
            self.__active_task_lock.acquire()
            #self.__logger.debug( "Active tasks num =%d" % (len(self.__active_tasks)) ) 
            for task in self.__active_tasks:
                self.__active_task_lock.release()
                task.wait()
                break
            else:
                self.__active_task_lock.release()
                #self.__logger.debug("all active tasks are all finished and wait finished")     
                break  
                              
    def get_ncpus(self):
        """Returns the number of local worker processes (ppworkers)"""
        return self.__ncpus

    def set_ncpus(self, ncpus="autodetect"):
        """Sets the number of local worker processes (ppworkers)

        ncpus - the number of worker processes, if parammeter is omitted
                it will be set to the number of processors in the system"""
        if ncpus == "autodetect":
            ncpus = self.__detect_ncpus()
        if not isinstance(ncpus, int):
            raise TypeError("ncpus must have 'int' type")
        if ncpus < 0:
            raise ValueError("ncpus must be an integer > 0")
        if ncpus > len(self.__workers):
            self.__workers.extend([_Worker(self.__restart_on_free, 
                    self.__pickle_proto) for x in\
                    range(ncpus - len(self.__workers))])
        self.__stats["local"].ncpus = ncpus
        self.__ncpus = ncpus

    def get_active_nodes(self):
        """Returns active nodes as a dictionary
        [keys - nodes, values - ncpus]"""
        active_nodes = {}
        for node, stat in self.__stats.items():
            if node == "local" or node in self.autopp_list \
                    and self.autopp_list[node]:
                active_nodes[node] = stat.ncpus
        return active_nodes

    def get_stats(self):
        """Returns job execution statistics as a dictionary"""
        for node, stat in self.__stats.items():
            if stat.rworker:
                try:
                    stat.rworker.send("TIME")
                    stat.time = float(stat.rworker.receive())
                except:
                    self.__accurate_stats = False
                    stat.time = 0.0
        return self.__stats
        
    def print_stats(self):
        """Prints job execution statistics. Useful for benchmarking on
           clusters"""

        print "Job execution statistics:"
        walltime = time.time()-self.__creation_time
        statistics = self.get_stats().items()
        totaljobs = 0.0
        for ppserver, stat in statistics:
            totaljobs += stat.njobs
        print " job count | % of all jobs | job time sum | " \
                "time per job | job server"
        for ppserver, stat in statistics:
            if stat.njobs:
                print "    %6i |        %6.2f |     %8.4f |  %11.6f | %s" \
                        % (stat.njobs, 100.0*stat.njobs/totaljobs, stat.time,
                        stat.time/stat.njobs, ppserver, )
        print "Time elapsed since server creation", walltime

        if not self.__accurate_stats:
            print "WARNING: statistics provided above is not accurate" \
                  " due to job rescheduling"
        print

    # all methods below are for internal use only
    
    def insert(self, sfunc, sargs, task=None):
        """Inserts function into the execution queue. It's intended for
           internal use only (ppserver.py).
        """
        if not task:
            tid = self.__gentid()
            task = _Task(self, tid)
        self.__queue_lock.acquire()
        self.__queue.append((task, sfunc, sargs))
        self.__queue_lock.release()

        self.__logger.debug("Task %i inserted" % (task.tid, ))
        self.__scheduler()
        return task

    def connect1(self, host, port, persistent=True):
        """Conects to a remote ppserver specified by host and port"""
        try:
            rworker = _RWorker(host, port, self.secret, "STAT", persistent)
            ncpus = int(rworker.receive())
            hostid = host+":"+str(port)
            self.__stats[hostid] = _Statistics(ncpus, rworker)

            for x in range(ncpus):
                rworker = _RWorker(host, port, self.secret, "EXEC1", persistent)
                self.__update_active_rworkers(rworker.id, 1)
                # append is atomic - no need to lock self.__rworkers
                self.__rworkers.append(rworker)
            #creating reserved rworkers
            for x in range(ncpus):
                rworker = _RWorker(host, port, self.secret, "EXEC1", persistent)
                self.__update_active_rworkers(rworker.id, 1)
                self.__rworkers_reserved.append(rworker)
            #creating reserved4 rworkers
            for x in range(ncpus*0):
                rworker = _RWorker(host, port, self.secret, "EXEC1", persistent)
#               self.__update_active_rworkers(rworker.id, 1)
                self.__rworkers_reserved4.append(rworker)
            logging.debug("Connected to ppserver (host=%s, port=%i) \
                    with %i workers" % (host, port, ncpus))
            self.__scheduler()
        except:
            pass
#           sys.excepthook(*sys.exc_info())

    def connect2(self, host, port, persistent=True):
        """Conects to a remote ppserver specified by host and port"""
        try:
            rworker = _RWorker(host, port, self.secret, "STAT", persistent)
            ncpus = int(rworker.receive())
            hostid = host+":"+str(port)
            self.__stats[hostid] = _Statistics(ncpus, rworker)
            
            rworker_reset = _RWorker(host, port, self.secret, "RESET", persistent)
            rworker_reset.receive()
            self.__rworkers_reset.append(rworker_reset)

            for x in range(ncpus):
                rworker = _RWorker(host, port, self.secret, "EXEC2", persistent)
                self.__update_active_rworkers(rworker.id, 1)
                # append is atomic - no need to lock self.__rworkers
                self.__rworkers.append(rworker)
            #creating reserved rworkers
            for x in range(ncpus):
                rworker = _RWorker(host, port, self.secret, "EXEC2", persistent)
#               self.__update_active_rworkers(rworker.id, 1)                
                self.__update_active_rworkers(rworker.id, 1)
                self.__rworkers_reserved.append(rworker)
            #creating reserved4 rworkers
            for x in range(ncpus*0):
                rworker = _RWorker(host, port, self.secret, "EXEC2", persistent)
                self.__rworkers_reserved4.append(rworker)
            logging.debug("Connected to ppserver (host=%s, port=%i) \
                    with %i workers" % (host, port, ncpus))
            self.__scheduler()
        except:
            pass

    def __connect(self, jobInserttype):
        """Connects to all remote ppservers"""
        if jobInserttype == 1:      
            for ppserver in self.ppservers:
                thread.start_new_thread(self.connect1, ppserver)
        if jobInserttype == 2:  
            for ppserver in self.ppservers:
                thread.start_new_thread(self.connect2, ppserver)           

        discover = ppauto.Discover(self, True)
        for ppserver in self.auto_ppservers:
            thread.start_new_thread(discover.run, ppserver)

    def __detect_ncpus(self):
        """Detects the number of effective CPUs in the system"""
        #for Linux, Unix and MacOS
        if hasattr(os, "sysconf"):
            if "SC_NPROCESSORS_ONLN" in os.sysconf_names:
                #Linux and Unix
                ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
                if isinstance(ncpus, int) and ncpus > 0:
                    return ncpus
            else:
                #MacOS X
                return int(os.popen2("sysctl -n hw.ncpu")[1].read())
        #for Windows
        if "NUMBER_OF_PROCESSORS" in os.environ:
            ncpus = int(os.environ["NUMBER_OF_PROCESSORS"])
            if ncpus > 0:
                return ncpus
        #return the default value
        return 1

    def __initlog(self, loglevel, logstream):
        """Initializes logging facility"""
        log_handler = logging.StreamHandler(logstream)
        log_handler.setLevel(loglevel)
        LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
        log_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        self.__logger = logging.getLogger('')
        self.__logger.addHandler(log_handler)
        self.__logger.setLevel(loglevel)

    def __dumpsfunc(self, funcs, modules):
        """Serializes functions and modules"""
        hashs = hash(funcs + modules)
        if hashs not in self.__sfuncHM:
            sources = [self.__get_source(func) for func in funcs]
            self.__sfuncHM[hashs] = pickle.dumps(
                    (funcs[0].func_name, sources, modules),
                    self.__pickle_proto)
        return self.__sfuncHM[hashs]

    def __find_modules(self, prefix, dict):
        """recursively finds all the modules in dict"""
        modules = []
        for name, object in dict.items():
            if isinstance(object, types.ModuleType) \
                    and name not in ("__builtins__", "pp"):
                if object.__name__ == prefix+name or prefix == "":
                    modules.append(object.__name__)
                    modules.extend(self.__find_modules(
                            object.__name__+".", object.__dict__))
        return modules

    def __scheduler(self): 
     
        # Schedules jobs for execution
        self.__queue_lock.acquire()
        while self.__queue:
            self.__logger.debug("scheduler %d tasks" % (len(self.__queue) ))
            if self.__active_localtask_Num < self.__ncpus:
                #TODO: select a job number on the basis of heuristic
                task = self.__queue.pop(0)
                for worker in self.__workers:
                    if worker.is_free:
                        worker.is_free = False
                        worker.HaveUsed = True
                        break
                else:
                    self.__logger.error("There are no free workers left")
                    raise RuntimeError("Error: No free workers")
                try:
                    self.__logger.debug("scheduler new thread of No.%d tasks(local) " % (list(task)[0].tid ))
                    self.__add_one_active_tasks(list(task)[0], 1)
                    self.__stats["local"].njobs += 1
                    thread.start_new_thread(self.__run, task+(worker, ))
                except:
                    worker.is_free = True 
                    worker.HaveUsed = False
                    self.__remove_one_active_tasks(list(task)[0], 1)
                    self.__stats["local"].njobs -= 1
                    pass
            else:
                for rworker in self.__rworkers:
                    if rworker.is_free:                 
                        rworker.is_free = False
                        rworker.HaveUsed = True                        
                        task = self.__queue.pop(0)
                        self.__logger.debug("scheduler new thread of No.%d tasks(remote)" % (list(task)[0].tid ))
                        self.__add_one_active_tasks(list(task)[0])
                        self.__stats[rworker.id].njobs += 1
                        thread.start_new_thread(self.__rrun, task+(rworker, ))
                        break
                else:
                    if len(self.__queue) > self.__ncpus:
                        for rworker in self.__rworkers_reserved:
                            if rworker.is_free:
                                rworker.is_free = False
                                rworker.HaveUsed = True
                                task = self.__queue.pop(0)
                                self.__add_one_active_tasks(list(task)[0])  
                                self.__stats[rworker.id].njobs += 1
                                thread.start_new_thread(self.__rrun,
                                        task+(rworker, ))
                                break
                        else:
                            break
                            # this code will not be executed
                            # and is left for further releases
                            if len(self.__queue) > self.__ncpus*0:
                                for rworker in self.__rworkers_reserved4:
                                    if rworker.is_free:
                                        rworker.is_free = False
                                        rworker.HaveUsed = True
                                        task = self.__queue.pop(0)
                                        self.__add_one_active_tasks(list(task)[0]) 
                                        self.__stats[rworker.id].njobs += 1
                                        thread.start_new_thread(self.__rrun,
                                                task+(rworker, ))
                                        break
                    else:
                        break
        self.__queue_lock.release()        

    def __rrun(self, job, sfunc, sargs, rworker, DoIter=1):
        """Runs a job remotelly"""
        self.__logger.debug("server run: Task (remote) %i started" % (job.tid, ))
        #Try to send sfunc and sargs to server. If failed, scheduler and connect to server again
        try:
            rworker.csend(sfunc)
            rworker.send(sargs)            
        except:
            self.__logger.debug("ERROR server run: Task (remote) %i could not send info to server!" % (job.tid, )) 
            self.__logger.debug("Task %i failed due to broken network " \
                    "connection - rescheduling" % (job.tid, ))
            self.insert(sfunc, sargs, job)
            self.__scheduler()
            self.__update_active_rworkers(rworker.id, -1)
            if rworker.connect(rworker.message):
                self.__update_active_rworkers(rworker.id, 1)
                self.__scheduler()
            return
        #Try to get result from server. If failed, scheduler and connect to server again      
        try:
            sresult = rworker.receive()
        except:
            self.__logger.debug("ERROR server run: Task (remote) %i could not accept info from server!" % (job.tid, ))
            self.__logger.debug("Task %i failed due to broken network " \
                    "connection - rescheduling" % (job.tid, ))
            self.insert(sfunc, sargs, job)
            self.__scheduler()
            self.__update_active_rworkers(rworker.id, -1)
            if rworker.connect(rworker.message):
                self.__update_active_rworkers(rworker.id, 1)
                self.__scheduler()
            return
            
        # block the current __rrun thread untill finished
        rworker.is_free = True
        job.finalize(sresult)

        # remove the job from the waiting list
        self.__waittasks_lock.acquire() 
        if job in self.__waittasks:
            self.__waittasks.remove(job)
        self.__waittasks_lock.release()
                
        # remove the job from the active task list        
        self.__remove_one_active_tasks(job)

        self.__logger.debug("Remote task %i ended" % (job.tid, ))
         
        # to perform iteration with the protection of dead-lock iteration
        self.__IterNum_lock.acquire()
        self.__IterNum += 1
        if self.__IterNum > 100:
            self.__IterNum -= 1
            self.__IterNum_lock.release()  
            return  
        else:
            self.__IterNum_lock.release()         
        # do iteration if needed
        if DoIter:  self.__scheduler() 
        self.__IterNum_lock.acquire()           
        self.__IterNum -= 1 
        self.__IterNum_lock.release() 

        
    def __run(self, job, sfunc, sargs, worker, DoIter=1):
        """Runs a job locally"""
        if self._exiting:
            return
            
        self.__logger.debug("local run: Task %i started, id=%d, pid=%d, sargs=%s." % (job.tid, id(job), worker.pid, sargs))
        start_time = time.time()
        #Try to send (sfunc, sargs) to local server and get result(sresult) back from local server
        try:
            worker.t.csend(sfunc)
            worker.t.send(sargs)
            sresult = worker.t.receive()
        except:
            if self._exiting:
                return
            else:
                sys.excepthook(*sys.exc_info())
                sresult = None
        # block the current __run thread untill finished
        worker.free()        
        job.finalize(sresult)

        # remove the job from the waiting list
        self.__waittasks_lock.acquire() 
        if job in self.__waittasks:
            self.__waittasks.remove(job)
        self.__waittasks_lock.release()
                
        # remove the job from the active task list     
        self.__remove_one_active_tasks(job, 1)  
        
        # add calculation time information             
        if not self._exiting:
            self.__stat_add_time("local", time.time()-start_time)            
        self.__logger.debug("local Task %i ended" % (job.tid, ))
              
        # to perform iteration with the protection of dead-lock iteration 
        self.__IterNum_lock.acquire()
        self.__IterNum += 1
        if self.__IterNum > 100:
            self.__IterNum -= 1
            self.__IterNum_lock.release()  
            return  
        else:
            self.__IterNum_lock.release() 
        # do iteration if needed
        if DoIter:  self.__scheduler() 
        self.__IterNum_lock.acquire()           
        self.__IterNum -= 1 
        self.__IterNum_lock.release() 

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
         
    def __add_one_active_tasks(self, task, num=0):
        """Updates the number of local active tasks"""
        self.__active_task_lock.acquire()
        self.__active_localtask_Num += num 
        self.__active_tasks.append(task)
        self.__active_task_lock.release()          
    
    def __remove_one_active_tasks(self, task, num=0):
        """Updates the number of active tasks"""
        self.__active_task_lock.acquire()
        self.__active_localtask_Num -= num
        self.__active_tasks.remove(task)
        self.__active_task_lock.release()
        
    def __stat_add_time(self, node, time_add):
        """Updates total runtime on the node"""
        self.__stats_lock.acquire()
        self.__stats[node].time += time_add
        self.__stats_lock.release()

    def __stat_add_job(self, node):
        """Increments job count on the node"""
        self.__stats_lock.acquire()
        self.__stats[node].njobs += 1
        self.__stats_lock.release()

    def __update_active_rworkers(self, id, count):
        """Updates list of active rworkers"""
        self.__active_rworkers_list_lock.acquire()

        if id not in self.autopp_list:
            self.autopp_list[id] = 0
        self.autopp_list[id] += count

        self.__active_rworkers_list_lock.release()

    def __gentid(self):
        """Generates a unique job ID number"""
        self.__tid += 1
        return self.__tid - 1
        
    def get_rworker_num(self):
        logging.debug("local worker=%d remote worker=%d" % \
            (len(self.__workers),len(self.__rworkers)))
        return len(self.__rworkers)
        
    def get_worker_num(self):
        logging.debug("local worker=%d remote worker=%d" % \
            (len(self.__workers),len(self.__rworkers)))
        return (len(self.__workers)+len(self.__rworkers))

    def get_server_num(self):
        server = {}
        server['local'] = 1          
        for rworker in self.__rworkers:
            if server.has_key(rworker.host):   continue
            server[rworker.host] = 1  
        logging.debug("server num = %d" % (len(server)))                      
        return (len(server))
        
    def get_class_hierarchy(clazz):
        classes = []
        if clazz is type(object()):
            return classes
        for base_class in clazz.__bases__:
            classes.extend(get_class_hierarchy(base_class))
        classes.append(clazz)
        return classes

    def is_not_imported(arg, modules):
        args_module = str(arg.__module__)
        for module in modules:
            if args_module == module or args_module.startswith(module + "."):
                return False
        return True

    def sortRWorker(self):
        keys = []
        rworkerDict = {}
        for item in self.ppservers:
            strItem = str(item[0])+':'+str(item[1])
            keys.append(strItem)
            rworkerDict[strItem] = []
        for rworker in self.__rworkers:
            strItem = str(rworker.host)+':'+str(rworker.port)
            rworkerDict[strItem].append(rworker)
        self.__rworkers = []
        for key in keys:
            self.__rworkers = self.__rworkers + rworkerDict[key]
        return True
            
    def destroy(self):
        """Kills ppworkers and closes open files"""
        self._exiting = True
        self.__queue_lock.acquire()
        self.__queue = []
        self.__queue_lock.release()

        for worker in self.__workers:
            worker.t.close()
            if sys.platform.startswith("win"):
                os.popen('TASKKILL /PID '+str(worker.pid)+' /F')
            else:
                try:
                    os.kill(worker.pid, 9)
                    os.waitpid(worker.pid, 0)
                except:
                    pass
                    
     #***********************************************************************************************
    # The below function three function is used to submit all the job first
    # and then implement all the job in parallel in the same time
     #***********************************************************************************************
     #-----------------------
     #    submitToQueue
     #-----------------------
    def submitToQueue (self, func, args=(), depfuncs=(), modules=(),\
                       callback=None, callbackargs=(), group='default', globals=None):  
         
        """only submit the job to queues and don't do any task"""
                   
        # perform some checks for frequent mistakes
        if self._exiting:
            raise RuntimeError("Cannot submit jobs: server instance has been destroyed")

        if not isinstance(args, tuple):
            raise TypeError("args argument must be a tuple")

        if not isinstance(depfuncs, tuple):
            raise TypeError("depfuncs argument must be a tuple")

        if not isinstance(modules, tuple):
            raise TypeError("modules argument must be a tuple")

        if not isinstance(callbackargs, tuple):
            raise TypeError("callbackargs argument must be a tuple")

        for module in modules:
            if not isinstance(module, types.StringType):
                raise TypeError("modules argument must be a list of strings")

        tid = self.__gentid()
        if globals:
            modules += tuple(self.__find_modules("", globals))
            modules = tuple(set(modules))
            self.__logger.debug("Task %i will autoimport next modules: %s" %
                    (tid, str(modules)))
            for object1 in globals.values():
                if isinstance(object1, types.FunctionType) \
                        or isinstance(object1, types.ClassType):
                    depfuncs += (object1, )

        task = _Task(self, tid, callback, callbackargs, group)

        self.__waittasks_lock.acquire()
        self.__waittasks.append(task)
        self.__waittasks_lock.release()

        # if the function is a method of a class add self to the arguments list
        if isinstance(func, types.MethodType) and func.im_self is not None:
            args = (func.im_self, ) + args

        # if there is an instance of a user deined class in the arguments add
        # whole class to dependancies
        for arg in args:
            # Checks for both classic or new class instances
            if isinstance(arg, types.InstanceType) \
                    or str(type(arg))[:6] == "<class":
                # do not include source for imported modules
                if ppcommon.is_not_imported(arg, modules):
                    depfuncs += tuple(ppcommon.get_class_hierarchy(arg.__class__))

        # if there is a function in the arguments add this
        # function to dependancies
        for arg in args:
            if isinstance(arg, types.FunctionType):
                depfuncs += (arg, )

        sfunc = self.__dumpsfunc((func, ) + depfuncs, modules)
        sargs = pickle.dumps(args, self.__pickle_proto)

        self.__queue_lock.acquire()
        self.__queue.append((task, sfunc, sargs))
        self.__queue_lock.release()

        self.__logger.debug("Task %i submited, function='%s'" %(tid, func.func_name))  

     #-----------------------
     # BatchDoJob
     #-----------------------   
    def BatchDoJob(self):
        """Batch do the all the jobs in Queue averagely by all the workers in system"""    

        for worker in self.__rworkers_reset:
            worker.send("RESET")
                   
        self.__queue_lock.acquire()
        jobNum =  len(self.__queue)   
        task_list = [] 
        while self.__queue:        
                     
            for item in self.__queue:
                a,b,c = item
                task_list.append(a)
                                                                                     
            for worker in self.__workers:                            
                worker.is_free  = False 
                worker.HaveUsed = True                
                task = self.__queue.pop(0)
                self.__add_one_active_tasks(list(task)[0], 1)
                self.__stats["local"].njobs += 1
                thread.start_new_thread(self.__run, task+(worker, )+(0,)) # DoIter=0,no iteration
                jobNum -= 1
                if jobNum == 0:              
                    self.__queue_lock.release()
                    return (task_list, 0)
                time.sleep(0.001)

            for rworker in self.__rworkers:                                                          
                rworker.is_free  = False
                rworker.HaveUsed = True 
                task = self.__queue.pop(0)
                self.__add_one_active_tasks(list(task)[0])
                self.__stats[rworker.id].njobs += 1
                thread.start_new_thread(self.__rrun, task+(rworker, )+(0,))# DoIter=0,no iteration  
                jobNum -= 1
                if jobNum == 0:                        
                    self.__queue_lock.release()           
                    return (task_list, 0)  	
                time.sleep(1)
            #break;                     
        self.__queue_lock.release()  
        return (task_list, jobNum)

     #-----------------------
     # insert_1worker_1job
     #-----------------------   
    def insert_1worker_1job (self, sfunc, sargs, task=None):
        """Inserts function into the execution queue. It's intended for internal use only by ppserver.py.
        one worker will do one job averagely.""" 
                      
        self.__queue_lock.acquire()
        if not task:
            tid = self.__gentid()
            task = _Task(self, tid)
            
        self.__logger.debug("Begin insert_1worker_1job:  = %d" %(tid))                     
        self.__waittasks_lock.acquire()
        self.__waittasks.append(task)
        self.__waittasks_lock.release() 
        self.__queue.append((task, sfunc, sargs))
        self.__queue_lock.release()  
                 
        self.DoJob_1worker_1job()
        self.__logger.debug("Finish insert_1worker_1job:  = %d" %(tid))                    
        return task

     #-----------------------
     # DoJob_1worker_1job
     #-----------------------   
    def DoJob_1worker_1job (self): 
        """ one worker do one job averagely """ 
                                       
        self.__queue_lock.acquire()               
        while self.__queue:
            self.__logger.debug("DoJob_1worker_1job begin:taskNum = %d" %(len(self.__queue))) 
                                
            IsLocalAllUsed = False
            IsRmoteAllUsed = False
            task = self.__queue.pop(0)
                        
            # Do job by local workers which are not only free, but also unused                          
            for worker in self.__workers:            
                self.ResetWhenAllUsed()                           
                if not worker.HaveUsed and worker.is_free:
                    worker.is_free  = False 
                    worker.HaveUsed = True
                    break
            else:
                IsLocalAllUsed = True                        
            if not IsLocalAllUsed:              
                self.__add_one_active_tasks(list(task)[0], 1)
                self.__stats["local"].njobs += 1
                thread.start_new_thread(self.__run, task+(worker,)+(0,)) 
                continue
                
            # Do job by remote workers which are not only free, but also unused                                                                                                     
            for rworker in self.__rworkers:
                self.ResetWhenAllUsed()
                if not rworker.HaveUsed and rworker.is_free:
                    rworker.is_free = False
                    rworker.HaveUsed = True
                    break;
            else:
                IsRmoteAllUsed = True 
            if not IsRmoteAllUsed:                                                          
                self.__add_one_active_tasks(list(task)[0])                
                self.__stats[rworker.id].njobs += 1
                thread.start_new_thread(self.__rrun, task+(rworker,)+(0,))
                continue    
                            
        self.__logger.debug("DoJob_1worker_1job finish:taskNum = %d" %(len(self.__queue)))                 
        self.__queue_lock.release()
        return        

     #-----------------------
     #ResetWhenAllUsed
     #-----------------------
    def ResetWhenAllUsed(self):
        """Reset all the HaveUsed flag of workers to be False when all workers' HaveUsed 
        flag are True."""
    
        IsLocalAllUsed = False
        IsRmoteAllUsed = False
        # To jude if all local workers have been used    
        for worker in self.__workers:
            if not worker.HaveUsed:     break;
        else:   
            IsLocalAllUsed = True
        # To judege if all remote workers have been used
        for rworker in self.__rworkers:
            if not rworker.HaveUsed:     break;
        else:   
            IsRmoteAllUsed = True  
        # If all remote workers are used
        if IsLocalAllUsed and IsRmoteAllUsed:          
            #wait untill all alive tasks are finished 
            self.waitAliveTask() 
            #reset HaveUsed flag to be False 
            for worker in self.__workers:   
                worker.HaveUsed = False;                 
            for rworker in self.__rworkers: 
                rworker.HaveUsed = False; 

    def ResetHaveUsed(self):
        """Reset all the HaveUsed flag of workers to be False when all workers' HaveUsed 
        flag are True."""
        
        #wait untill all alive tasks are finished 
        self.waitAliveTask()
        #reset HaveUsed flag to be False 
        for worker in self.__workers:
            worker.HaveUsed = False;

        for rworker in self.__rworkers:
            rworker.HaveUsed = False;
            
     #***********************************************************************************************
    # The below function three function is used to submit one job and do it across a tree
     #***********************************************************************************************                                                            
     #-----------------------
     #insert_BatchTreeDoJob
     #-----------------------
    def insert_BatchTreeDoJob (self, sfunc, sargs, task=None):
        """Inserts function into the execution queue. It's intended for internal use only by ppserver.py.
        one worker will do one job averagely.""" 
                      
        self.__queue_lock.acquire()
        if not task:
            tid = self.__gentid()
            task = _Task(self, tid)
            
        self.__logger.debug("Begin insert_1worker_1job:  = %d" %(tid))                     
        self.__waittasks_lock.acquire()
        self.__waittasks.append(task)
        self.__waittasks_lock.release() 
        self.__queue.append((task, sfunc, sargs))
        self.__queue_lock.release()  
        # batch tree do job
        self.BatchTreeDoJob()
        self.__logger.debug("Finish insert_1worker_1job:  = %d" %(tid))                    
        return task                               

     #-----------------------
     # BatchTreeDoJob
     #-----------------------                               
    def BatchTreeDoJob(self):
        """Batch do the all the jobs in Queue averagely by all the workers in system"""    

        for worker in self.__rworkers_reset:
            worker.send("RESET")
                   
        self.__queue_lock.acquire()
        if len(self.__queue) != 1:
            self.__logger.error("BatchTreeDoJob mode only allow one task to be inserted in self.__queue")
            raise RuntimeError("Error: more than one task in queue for BatchTreeDoJob")
        # get expected job num 
        jobNum = len(self.__workers) 
        serverFlag = {}
        for rworker in self.__rworkers:
            if serverFlag.has_key(rworker.host): 
                continue 
            jobNum += 1  
        
        #create tasks for current server machine
        a,b,c = self.__queue[0]
        task_list[a]        
        for ii in xrange(jobNum-1):                                            
            tid = self.__gentid()
            task = _Task(self, tid)
            self.__queue.append((task, b, c))
            task_list.append(task)
            
        #all local workers will all be actived   
        for worker in self.__workers:                            
            worker.is_free  = False 
            worker.HaveUsed = True                
            task = self.__queue.pop(0)
            self.__add_one_active_tasks(list(task)[0], 1)
            self.__stats["local"].njobs += 1
            thread.start_new_thread(self.__run, task+(worker, )+(0,)) # DoIter=0,no iteration
            time.sleep(0.001)
                
        #each server machines will be assigned one task
        serverFlag = {}
        for rworker in self.__rworkers:
            if serverFlag.has_key(rworker.host): continue                                                       
            rworker.is_free  = False
            rworker.HaveUsed = True 
            task = self.__queue.pop(0)
            self.__add_one_active_tasks(list(task)[0])
            self.__stats[rworker.id].njobs += 1
            thread.start_new_thread(self.__rrun, task+(rworker, )+(0,))# DoIter=0,no iteration  
     
        self.__queue_lock.release() 

        #perform results of task_list and store in task_list[0]
        task_list[0]()
        result0    = (task_list[0]).result 
        sout0      = (task_list[0]).sout
        if result0 == None: 
            task_list[0].sresult = pickle.dumps(None, sout0, self.__pickle_proto)
            return task_list[0]
        else:
            for task in task_list[1:]:  
                result = task.result
                sout   =  task.sout
                assert (result != None)
                #merge begin
                if (type(result) == type(0.) and type(result0) == type(0.)) or (type(result) == type(0) and type(result0) == type(0)):
                    result0 = result0 + result                 
                elif type(result) == type('string') and type(result0) == type('string'):
                    #Add two strng of float array together ( module stringMerge is build from outside)
                    import stringMerge
                    cMergeClass = cResultMerge()
                    cMergeClass.AddStringOfFloatArray (result0, result) # add float array of string result to result0
                else:
                    print "BatchTreeDoJob\t mering process could only support int, float and string type merging!"
                    exit(1)
                #merge end       
        task_list[0].sresult = pickle.dumps (result0, sout0, self.__pickle_proto)  
        return task_list[0]
                                
# Parallel Python Software: http://www.parallelpython.com
