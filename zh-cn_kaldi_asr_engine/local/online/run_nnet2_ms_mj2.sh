#!/bin/bash
date -R
# This is the "multi-splice" version of the online-nnet2 training script.
# It's currently the best recipe.
# You'll notice that we splice over successively larger windows as we go deeper
# into the network.

. cmd.sh


stage=0
train_stage=-10
use_gpu=true
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

# do the common parts of the script.
#local/online/run_nnet2_common_mj2.sh --stage $stage


if [ $stage -le 7 ]; then
  if [[ $(hostname -f) == *.clsp.jhu.edu ]] && [ ! -d $dir/egs/storage ]; then
    utils/create_split_dir.pl \
     /export/b0{3,4,5,6}/$USER/kaldi-data/egs/librispeech-$(date +'%m_%d_%H_%M')/s5/$dir/egs/storage $dir/egs/storage
  fi

  # The size of the system is kept rather smaller than the run_7a_960.sh system:
  # this is because we want it to be small enough that we could plausibly run it
  # in real-time.
  steps/nnet2/train_multisplice_accel2_mj2.sh --stage $train_stage \
    --num-epochs 8 --num-jobs-initial 2 --num-jobs-final 2 \
    --num-hidden-layers 6 --splice-indexes "layer0/-2:-1:0:1:2 layer1/-1:2 layer3/-3:3 layer4/-7:2" \
    --feat-type raw \
    --online-ivector-dir exp/nnet2_online/ivectors_train_960_hires \
    --cmvn-opts "--norm-means=false --norm-vars=false" \
    --num-threads "$num_threads" \
    --minibatch-size "$minibatch_size" \
    --parallel-opts "$parallel_opts" \
    --io-opts "--max-jobs-run 12" \
    --initial-effective-lrate 0.0015 --final-effective-lrate 0.00015 \
    --cmd "$decode_cmd" \
    --pnorm-input-dim 3500 \
    --pnorm-output-dim 350 \
    --mix-up 12000 \
    data/train_960_hires data/lang exp/tri6b $dir  || exit 1;
fi

date -R

exit 0;
