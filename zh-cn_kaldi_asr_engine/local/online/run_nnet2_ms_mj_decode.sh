#!/bin/bash

# This is the "multi-splice" version of the online-nnet2 training script.
# It's currently the best recipe.
# You'll notice that we splice over successively larger windows as we go deeper
# into the network.

. cmd.sh


stage=0
train_stage=-10
use_gpu=false
dir=exp/nnet2_online/nnet_ms_a

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

  if [[ $(hostname -f) == *.clsp.jhu.edu ]]; then
    parallel_opts="$parallel_opts --config conf/queue_no_k20.conf --allow-k20 false"
    # that config is like the default config in the text of queue.pl, but adding the following lines.
    # default allow_k20=true
    # option allow_k20=true
    # option allow_k20=false -l 'hostname=!g01&!g02&!b06'
    # It's a workaround for an NVidia CUDA library bug for our currently installed version
    # of the CUDA toolkit, that only shows up on k20's
  fi
  # the _a is in case I want to change the parameters.
else
  # Use 4 nnet jobs just like run_4d_gpu.sh so the results should be
  # almost the same, but this may be a little bit slow.
  num_threads=16
  minibatch_size=128
  parallel_opts="-pe smp $num_threads" 
fi

mfccdir=mfcc

#for datadir in test_clean test_other dev_clean dev_other; do
    #utils/copy_data_dir.sh data/$datadir data/${datadir}_hires
    #steps/make_mfcc.sh --nj 20 --mfcc-config conf/mfcc_hires.conf \
     # --cmd "$train_cmd" data/${datadir}_hires exp/make_hires/$datadir $mfccdir || exit 1;
    #steps/compute_cmvn_stats.sh data/${datadir}_hires exp/make_hires/$datadir $mfccdir || exit 1;
#done

if [ $stage -le 10 ]; then
  # If this setup used PLP features, we'd have to give the option --feature-type plp
  # to the script below.
  steps/online/nnet2/prepare_online_decoding.sh --mfcc-config conf/mfcc_hires.conf \
    data/lang exp/nnet2_online/extractor "$dir" ${dir}_online || exit 1;
fi

if [ $stage -le 11 ]; then
  # do the actual online decoding with iVectors, carrying info forward from 
  # previous utterances of the same speaker.
  for test in test_all_data; do
    steps/online/nnet2/decode.sh --config conf/decode.config --cmd "$decode_cmd" --nj 20 \
      exp/tri6b/graph_pp_tgsmall data/$test ${dir}_online/decode_pp_${test}_tgsmall || exit 1;
    #steps/lmrescore.sh --cmd "$decode_cmd" data/lang_pp_test_{tgsmall,tgmed} \
      #data/$test ${dir}_online/decode_pp_${test}_{tgsmall,tgmed}  || exit 1;
    #steps/lmrescore_const_arpa.sh \
      #--cmd "$decode_cmd" data/lang_pp_test_{tgsmall,tglarge} \
      #data/$test ${dir}_online/decode_pp_${test}_{tgsmall,tglarge} || exit 1;
    #steps/lmrescore_const_arpa.sh \
      #--cmd "$decode_cmd" data/lang_pp_test_{tgsmall,fglarge} \
      #data/$test ${dir}_online/decode_pp_${test}_{tgsmall,fglarge} || exit 1;
  done
fi

exit 0;
