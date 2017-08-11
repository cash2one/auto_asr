#!/bin/sh -x

##### 原始文件("0001.wav#你们去吃饭吧")存放到 data/text 中 可以多个

if(($# < 3))
then 
	echo "usage: $0 text_lab_dir text_train wav_dir"
	exit 0
fi

while(true)
do
    if [ -f lock ];then
        echo "当前流程有人使用，等待即可!  date:`date +%H:%M:%S`"
        sleep 2;
    else
        touch lock;
        echo "当前流程无人使用，我们现在开始......"
        break;
    fi
done


text_lab=$1
text_train=$2
wav_dir=$3

#result=decode_result.txt
result=ttt.log

pwd_dir=`pwd`

rm -rf lmtrain_for_auto/data/text/* 
rm -rf pplm.dict voc* 

### 文本处理
#rm -rf $text_lab.bak && cp -r $text_train $text_lab.bak
#sed -i 's/，\|。\|,\|《\|》\|\.\|(\|)\|“\|”\|-\|\t\| //g;s/（.*）//g' $text_train 
if [ -f "$text_train" ]; then
	cp -r $text_train lmtrain_for_auto/data/text/ 
elif [ -d "$text_train" ]; then
	cp -r $text_train/* lmtrain_for_auto/data/text/ 
else
    echo "file=${text_train} not exist !"
    rm -rf lock
    exit 0;
fi

### 训练语言模型 
cd lmtrain_for_auto 
    ./shell/lmtrain.sh 
cd -
if [ ! -f lmtrain_for_auto/data/lm/test.arpa.gz ];then
    echo "ERROR: LM训练失败！"
    exit 0;
fi

cp lmtrain_for_auto/data/lm/test.arpa.gz  lmtrain_for_auto/data/pplm.dict ./

#### --------------------------------------------------------

#### 注音 en-us_cmu: phonetisaurus	 
sed '1d' pplm.dict|awk -F"\t" '{print $2}' > voc

cd /home/szm/voc2py/mars/dict/util 
    perl make_raw_dict.pl -i $pwd_dir/voc -o $pwd_dir/voc.lex \
    -l zh-cn_pinyin -m lingua -e utf8 -w 1
cd -
if [ ! -f voc.lex ];then
    echo "ERROR: 注音失败!"
    exit 0;
fi

##### 识别
cd zh-cn_kaldi_asr_engine 

    rm -rf voc.lex test.arpa.gz 
    cp -r ../voc.lex ../test.arpa.gz ./ 
    ./run_zh_cn_decode_mj.sh voc.lex test.arpa.gz ../$wav_dir 

    cp -r ${result} ../

cd -


if [ ! -f ${result} ];then
    echo "ERROR:解码失败！"
    exit 0;
fi

##### WER
#grep -v "^#\|online\|wav-copy" decode_result.txt > decode_result.txt.grep
#
#awk -F" " '{printf $1".wav:";for(nn=2;nn<NF;nn++){printf $nn""}if(NF>=2){printf $NF} print ""}'      decode_result.txt.grep |sort -n  > decode_result.txt.grep.awk
#



#rm -rf wer_count/*.txt
#cp -r decode_result.txt.grep.awk wer_count/res.txt
#
#if [ -f "$text_lab" ]; then
#	cat $text_lab > wer_count/lab.txt
#elif [ -d "$text_lab" ]; then
#	cat $text_lab/* > wer_count/lab.txt
#fi
#cd wer_count && ./run.sh lab.txt res.txt wer.txt && rm -rf ../wer.txt && cp wer.txt ../ && cd -
#rm -rf decode_result.txt decode_result.txt.grep
#
####


rm -rf lock
