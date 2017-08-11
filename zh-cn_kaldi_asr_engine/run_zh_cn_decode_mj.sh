#!/bin/bash


# Set this to somewhere where you want to put your data, or where
# someone else has already put it.  You'll want to change this 
# if you're not on the CLSP grid.
decode_dict=$1
lm_compress=$2
data_wav=$3

. cmd.sh
. path.sh

# you might not want to do this for interactive shells.
set -e

dir=exp/nnet2_online/nnet_ms_a

threadnum=10

rm -rf data/local/lang_tmp
rm -rf data/local/dict
rm -rf data/local/lm/*
rm -rf data/lang*
rm -rf data/test_all_data
rm -rf exp/tri6b/graph_pp_tgsmall
rm -rf exp/nnet2_online/nnet_ms_a_online/
rm -rf decode_result.txt

## dispose dict
### pinyin to ph97
python local/create_dict_for_kaldi.py $decode_dict

### lm to data/local/lm
cp $lm_compress data/local/lm/lm_tgsmall.arpa.gz

## prepare data
python local/data_prep_mj_multi_folder.py $data_wav data/test_all_data

# when "--stage 3" option is used below we skip the G2P steps, and use the
# lexicon we have already downloaded from openslr.org/11/
local/prepare_dict.sh --stage 3 --nj $threadnum --cmd "$train_cmd" \
   data/local/lm data/local/lm data/local/dict || exit 1

utils/prepare_lang.sh data/local/dict "<SPOKEN_NOISE>" data/local/lang_tmp data/lang_pp || exit 1;

cp -r data/lang_pp data/lang

local/format_lms.sh --src-dir data/lang_pp data/local/lm

utils/mkgraph.sh data/lang_pp_test_tgsmall exp/tri6b exp/tri6b/graph_pp_tgsmall || exit 1;

steps/online/nnet2/prepare_online_decoding.sh --mfcc-config conf/mfcc_hires.conf \
    data/lang exp/nnet2_online/extractor "$dir" ${dir}_online || exit 1;


######## 1. 开始解码 
#for test in test_all_data; do
#
#    steps/online/nnet2/decode.sh --config conf/decode.config \
#    --cmd "$decode_cmd" --nj $threadnum exp/tri6b/graph_pp_tgsmall \
#    data/$test ${dir}_online/decode_pp_${test}_tgsmall || exit 1;
#
#done
#
### 识别结果整理 
#cat exp/nnet2_online/nnet_ms_a_online/decode_pp_test_all_data_tgsmall/log/decode.*.log >> decode_result.txt


##### 2. 开始多线程解码
max_active=7000
beam=15.0
lattice_beam=6.0
acwt=0.1   

graphdir=exp/tri6b/graph_pp_tgsmall
srcdir=exp/nnet2_online/nnet_ms_a_online


### spk 列表格式 
dir_wav=${data_wav}
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

### 得到结果 ttt.log 
###grep "^dir_wav" nohup.out |sort -n > dir_wav.res





