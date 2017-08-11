#!/bin/sh

dir_wav=$1
wav_list=ttt.testset.list
spk_list=ttt.spk.list

find  ${dir_wav}/ -iname "*.wav" > ttt
#awk '{print NR" "$0}' ttt > ${wav_list}
awk '{print $0}' ttt > ${wav_list}
awk '{print "spk_"NR" "NR}' ttt > ${spk_list}


