#-*- coding: utf-8 -*-
from __future__ import division
import os
import sys
import string
import commands


if len(sys.argv) < 4:
    print "usage %s res.txt lab.txt log.txt"%(sys.argv[0])
    sys.exit(0)


log_file=open(sys.argv[3],'w')
log_file.write("index\tlabel\twav\trecog\twer\n")

dict_res={}
res_file=open(sys.argv[1],'r')
for line in res_file.readlines():
    if line[-1] == '\n':
        line=line[:-1]
    idx_dot=line.find(' ')
    idx_wav=line[0:idx_dot]
    res=line[idx_dot+1:].strip()
    res_wav_up=res.upper()
    dict_res[idx_wav]=res_wav_up
    #print "%s\t%s"%(idx_wav,res)
    #print res_wav_up

### lab.txt
lab_file=open(sys.argv[2],'r')
for line in lab_file.readlines():
    if line[-1] == '\n':
        line=line[:-1]
    idx_dot=line.find('.')
    idx_wav=line[0:idx_dot]
    lab_wav=line[idx_dot+1:].strip()
    lab_wav_up=lab_wav.upper()
    dict_res['err']='err'
    idx_ok='err'
    wer_ok=1.0
    wer=1.0
    for k in dict_res.keys():
        #log_file.write("res_line k:%s  value:%s\n"%(k,dict_res[k]))
        cmd="./wer \"%s\" \"%s\""%(lab_wav_up,dict_res[k])
        (ret,out)=commands.getstatusoutput(cmd)
        #print out
        wer_str=out[out.find('werfloat:')+9:out.find('werint')]
        #print wer_str
        wer=string.atof(wer_str)
        #log_file.write("\t\t\twer:%f\t%s\n"%(wer,cmd))
        if wer < wer_ok:
            wer_ok=wer
            idx_ok=k

    if idx_ok != 'err':
        log_file.write("%s\t%s\t%s\t%s\t%f\n"%(idx_wav,lab_wav,idx_ok,dict_res[idx_ok],wer_ok))
        log_file.flush()

res_file.close()
lab_file.close()
log_file.close()
            

