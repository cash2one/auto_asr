#!/bin/bash

# this script contains some common (shared) parts of the run_nnet*.sh scripts.

. cmd.sh


stage=0

set -e
. cmd.sh
. ./path.sh
. ./utils/parse_options.sh



if [ $stage -le 5 ]; then
  # iVector extractors can in general be sensitive to the amount of data, but
  # this one has a fairly small dim (defaults to 100) so we don't use all of it,
  # we use just the 60k subset (about one fifth of the data, or 200 hours).
  steps/online/nnet2/train_ivector_extractor.sh --cmd "$train_cmd" --nj 5 \
    data/train_mixed_hires_60k exp/nnet2_online/diag_ubm exp/nnet2_online/extractor || exit 1;
fi

if [ $stage -le 6 ]; then
  ivectordir=exp/nnet2_online/ivectors_train_960_hires
  if [[ $(hostname -f) == *.clsp.jhu.edu ]] && [ ! -d $ivectordir/storage ]; then
    utils/create_split_dir.pl /export/b0{1,2,3,4}/$USER/kaldi-data/egs/librispeech-$(date +'%m_%d_%H_%M')/s5/$ivectordir/storage $ivectordir/storage
  fi
  # We extract iVectors on all the train data, which will be what we train the
  # system on.  With --utts-per-spk-max 2, the script.  pairs the utterances
  # into twos, and treats each of these pairs as one speaker.  Note that these
  # are extracted 'online'.
  steps/online/nnet2/extract_ivectors_online.sh --cmd "$train_cmd" --nj 20 \
    data/train_960_hires exp/nnet2_online/extractor $ivectordir || exit 1;
fi


exit 0;
