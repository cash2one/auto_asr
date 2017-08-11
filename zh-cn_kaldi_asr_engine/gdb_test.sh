#!/bin/bash -x

. cmd.sh
. path.sh

max_active=7000
beam=15.0
lattice_beam=6.0
acwt=0.1   

graphdir=exp/tri6b/graph_pp_tgsmall
srcdir=exp/nnet2_online/nnet_ms_a_online


### spk 列表格式 
dir_wav=../szm_wav
./creat_testset.sh  ${dir_wav}  

./online2-wav-nnet2-latgen-faster \
	--online=true --do-endpointing=false \
	--config=conf/decode.config \
    --config=$srcdir/conf/online_nnet2_decoding.conf \
    --max-active=$max_active --beam=$beam --lattice-beam=$lattice_beam \
    --acoustic-scale=$acwt \
    --word-symbol-table=${graphdir}/words.txt \
    ${srcdir}/final.mdl \
	${graphdir}/HCLG.fst \
	'ark:ttt.spk.list' \
    'ttt.testset.list'   ark:/dev/null

### ttt.log 就是结果
### grep "^${dir_wav}" ttt.log | sort -n -t/ -k3 > ${dir_wav}.res















########------------------------------------------------------------------------



###### v0-kaldi-bak
#./creat_testset_v0.sh  dir_wav
#./online2-wav-nnet2-latgen-faster \
#	--online=true --do-endpointing=true \
#	--config=decode_resource/nnet_ms_a_online/conf/online_nnet2_decoding.conf \
#	--max-active=7000 --beam=15.0 --lattice-beam=6.0 --acoustic-scale=0.1 \
#	--word-symbol-table=decode_resource/graph_pp_tgsmall/words.txt \
#	decode_resource/nnet_ms_a_online/final.mdl \
#	decode_resource/graph_pp_tgsmall/HCLG.fst \
#	'ark:dir_wav.spk.list' \
#	'scp:dir_wav.testset.list' ark:/dev/null

##### v4
#./creat_testset_v4.sh dir_wav
##### 不需要spk信息 识别测试 
#./online2-wav-nnet2-latgen-faster.v4 \
#	--online=true --do-endpointing=true \
#	--config=/home/mengjun/kaldi-master/src/online2bin/decode_resource/nnet_ms_a_online/conf/online_nnet2_decoding.conf \
#	--max-active=7000 --beam=15.0 --lattice-beam=6.0 --acoustic-scale=0.1 \
#	--word-symbol-table=/home/mengjun/kaldi-master/src/online2bin/decode_resource/graph_pp_tgsmall/words.txt \
#	/home/mengjun/kaldi-master/src/online2bin/decode_resource/nnet_ms_a_online/final.mdl \
#	/home/mengjun/kaldi-master/src/online2bin/decode_resource/graph_pp_tgsmall/HCLG.fst \
#	'ark:dir_wav.spk.list' \
#	'scp:dir_wav.testset.list'  ark:/dev/null



#valgrind   --leak-check=full  ./online2-wav-nnet2-latgen-faster \
#	--online=true --do-endpointing=true \
#	--config=/home/mengjun/kaldi-master/src/online2bin/decode_resource/nnet_ms_a_online/conf/online_nnet2_decoding.conf \
#	--max-active=7000 --beam=15.0 --lattice-beam=6.0 --acoustic-scale=0.1 \
#	--word-symbol-table=/home/mengjun/kaldi-master/src/online2bin/decode_resource/graph_pp_tgsmall/words.txt \
#	/home/mengjun/kaldi-master/src/online2bin/decode_resource/nnet_ms_a_online/final.mdl \
#	/home/mengjun/kaldi-master/src/online2bin/decode_resource/graph_pp_tgsmall/HCLG.fst \
#	'ark:dir_wav.spk.list' \
#	'scp:dir_wav.testset.list'  ark:/dev/null





###### server
###./creat_testset_v4.sh dir_wav
###### 不需要wav_list  
#./server \
#	--online=true --do-endpointing=true \
#	--config=/home/mengjun/kaldi-master/src/online2bin/decode_resource/nnet_ms_a_online/conf/online_nnet2_decoding.conf \
#	--max-active=7000 --beam=15.0 --lattice-beam=6.0 --acoustic-scale=0.1 \
#	--word-symbol-table=/home/mengjun/kaldi-master/src/online2bin/decode_resource/graph_pp_tgsmall/words.txt \
#	/home/mengjun/kaldi-master/src/online2bin/decode_resource/nnet_ms_a_online/final.mdl \
#	/home/mengjun/kaldi-master/src/online2bin/decode_resource/graph_pp_tgsmall/HCLG.fst \
#	8888  ark:/dev/null
#


