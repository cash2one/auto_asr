




test_wav  test.txt 测试语音和对应文本 

zh-cn_kaldi_asr_engine 内:
    gdb_test.sh 使用多线程版本
    kaldi-master  重新在src下 configure make 











===============================================================
lmtrain_for_auto中为处理文本、分词、选词典、训练arpa模型
	首先删除 data/text 中的文件，然后将要训练模型的文本放到这个目录下，可以有多个，大小不能超过2G
	文本格式为： 
		语音文件名字【tab】语音内容
		23454.wav	今天去哪里吃饭
		34543.wav	你们周末有时间么




test:

all_word_count 2006.000000	error_word 1233.000000
all_sent 148.000000	error_sent 116.000000
wer = 0.61466
word accuracy 0.38534
sentence accuracy 0.21622

