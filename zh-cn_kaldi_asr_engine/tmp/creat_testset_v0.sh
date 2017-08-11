#!/bin/sh

dir_wav=$1
wav_list=${dir_wav}.testset.list
spk_list=${dir_wav}.spk.list

find  ${dir_wav}/ -iname "*.wav" > ttt
#awk '{print NR" "$0}' ttt > ${wav_list}
awk '{print NR" "$0}' ttt > ${wav_list}
awk '{print "spk_"NR" "NR}' ttt > ${spk_list}


