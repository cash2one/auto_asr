#!/bin/sh -x 
#### 原始文件("0001.wav#文本")存放到 data/text 中 

vocab=vocab.txt
ngram_count=/usr/local/srilm/bin/i686-m64/ngram-count
pwd_dir=`pwd`

rm -rf data/text_awk/*
rm -rf data/seg/*
rm -rf data/cps_tree/*
rm -rf data/merge/*
rm -rf data/lm/test*

mkdir -p data/text_awk
mkdir -p data/text

### 分词
#seg_dir=/home/szm/cd/ICTCLAS2014/src/sample/c_seg
seg_dir=/home/szm/cd/mmseg-0.7.3
#export LD_LIBRARY_PATH=$seg_dir:$LD_LIBRARY_PATH
ls -1 data/text|while read line
do
	######  awk -F":" '{print $2}' data/text/$line > data/text_awk/$line
	#######  sed -i 's/，\|。\|,\|《\|》\|\.\|(\|)\|“\|”\|-\|\t\|、\|！\|？\|：\|；\|‘//g;s/（.*）//g' data/text_awk/$line
	rm -rf handleCorpus/$line
	cp -r data/text/$line  handleCorpus/
	cd handleCorpus && ./run.sh $line && cd -
	cp -r handleCorpus/$line.ok data/text_awk/$line
	
	cp -r data/text_awk/$line $seg_dir 
	cd $seg_dir && ./run.sh $line $line.seg && cd - 
	cp $seg_dir/$line.seg data/seg 
done

############################################ 选词典

cat data/seg/* > seg.all
python pysh/count.py seg.all seg.all.count  
sort -n -r seg.all.count > seg.all.count.sort

awk -F"\t" '{print NR"\t"$2}'  seg.all.count.sort > seg.all.count.sort.awk
awk -F"\t" '{print $2}'  seg.all.count.sort > ${vocab}

all_line=`wc -l seg.all.count.sort.awk|awk '{print $1}'`

sed "1i\
$all_line" seg.all.count.sort.awk > data/pplm.dict

#rm -rf seg.all*

####### 注音 去掉未能注音的词 重新生成词典 en-us_cmu: phonetisaurus	 
#sed '1d' data/pplm.dict|awk -F"\t" '{print $2}' > voc
#cd /home/szm/voc2py/mars/dict/util 
#perl make_raw_dict.pl -i $pwd_dir/voc -o $pwd_dir/voc.lex -l zh-cn_pinyin -m lingua -e utf8 -w 1
#cd -
#
#awk -F"\t" '{print $1}' voc.lex |awk -F"(" '{print $1}' |sort|uniq > voc.uniq
#awk -F"\t" '{print NR"\t"$0}'  voc.uniq > voc.uniq.awk
#all_line=`wc -l voc.uniq.awk|awk '{print $1}'`
#sed "1i\
#$all_line" voc.uniq.awk > data/pplm.dict


#################  srilm   #############################
#text_gz=text_all.gz
#lm_4=data/lm/test.arpa
#cat data/seg/* | gzip >  ${text_gz}
#
################## 4-gram 用于最终解码 
#${ngram_count} -order 4  -kndiscount -interpolate -unk -map-unk "<UNK>"    -limit-vocab -vocab $vocab -text ${text_gz} -lm ${lm_4} || exit 1
#
##${ngram_count} -order 4  -interpolate -unk -map-unk "<UNK>"  -text ${text_gz} -lm ${lm_4} || exit 1
#
#sed -i 's/<unk>/<UNK>/g'  ${lm_4}
#cat ${lm_4} | gzip > data/lm/test.arpa.gz
#
#################  pplm    ########################################

### 训练模型
ls -1 data/seg|while read line
do
	awk '{print 100"\t"$0}' data/seg/$line > data/seg/$line.tmp
	rm -rf data/seg/$line
done
ls -1 data/seg > data/list/cps.list.tmp
awk '{print "data/seg/"$0}' data/list/cps.list.tmp > data/list/cps.list
rm -rf data/list/cps.list.tmp
python pysh/ppCpsToTree.py conf/cps2tree.conf 

ls -1 data/cps_tree > data/list/cps_tree.list
python pysh/ppTrainLM.py conf/train.conf 


#### arpa格式
python pysh/ppInvertLM.py conf/invert.conf 

sed -i 's/<unk>/<UNK>/g' data/lm/test.arpa

cat data/lm/test.arpa | gzip > data/lm/test.arpa.gz

