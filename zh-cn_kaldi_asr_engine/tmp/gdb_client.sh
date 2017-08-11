#!/bin/bash




##### client
./creat_testset_v4.sh dir_wav
##### 不需要wav_list  
./client 127.0.0.1 8888 'scp:dir_wav.testset.list' 



