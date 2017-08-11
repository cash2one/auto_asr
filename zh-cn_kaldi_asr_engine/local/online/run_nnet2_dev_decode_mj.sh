#!/bin/bash

# example script for online-nnet2 system training and decoding,
# based on the one for fisher-English.

. cmd.sh


stage=0
train_stage=-10
use_gpu=true
dir=exp/nnet2_online/nnet_a

set -e
. cmd.sh
. ./path.sh
. ./utils/parse_options.sh


if $use_gpu; then
  if ! cuda-compiled; then
    cat <<EOF && exit 1 
This script is intended to be used with GPUs but you have not compiled Kaldi with CUDA 
If you want to use GPUs (and have them), go to src/, and configure and make on a machine
where "nvcc" is installed.  Otherwise, call this script with --use-gpu false
EOF
  fi
  parallel_opts="-l gpu=1" 
  num_threads=1
  minibatch_size=512
  # the _a is in case I want to change the parameters.
else
  # Use 4 nnet jobs just like run_4d_gpu.sh so the results should be
  # almost the same, but this may be a little bit slow.
  num_threads=16
  minibatch_size=128
  parallel_opts="-pe smp $num_threads" 
fi

mfccdir=mfcc

if [ $stage -le 9 ]; then
  # this does offline decoding that should give about the same results as the
  # real online decoding (the one with --per-utt true)
  for test in dev_clean dev_other; do
    
	steps/lmrescore_const_arpa.sh \
      --cmd "$decode_cmd" data/lang_test_{tgsmall,fglarge} \
      data/$test $dir/decode_${test}_{tgsmall,fglarge} || exit 1;
  done
fi

if [ $stage -le 11 ]; then
  # do the actual online decoding with iVectors, carrying info forward from 
  # previous utterances of the same speaker.
  for test in dev_clean dev_other; do
    
	steps/lmrescore_const_arpa.sh \
      --cmd "$decode_cmd" data/lang_test_{tgsmall,fglarge} \
      data/$test ${dir}_online/decode_${test}_{tgsmall,fglarge} || exit 1;
  done
fi

if [ $stage -le 12 ]; then
  # this version of the decoding treats each utterance separately
  # without carrying forward speaker information.
  for test in dev_clean dev_other; do
    
	steps/lmrescore_const_arpa.sh \
      --cmd "$decode_cmd" data/lang_test_{tgsmall,fglarge} \
      data/$test ${dir}_online/decode_${test}_{tgsmall,fglarge}_utt || exit 1;
  done
fi

if [ $stage -le 13 ]; then
  # this version of the decoding treats each utterance separately
  # without carrying forward speaker information, but looks to the end
  # of the utterance while computing the iVector (--online false)
  for test in dev_clean dev_other; do
  
	steps/lmrescore_const_arpa.sh \
      --cmd "$decode_cmd" data/lang_test_{tgsmall,fglarge} \
      data/$test ${dir}_online/decode_${test}_{tgsmall,fglarge}_utt_offline || exit 1;
  done
fi

exit 0;
