#!/bin/sh

##result=decode_result.txt
result=ttt.log
rm -rf ${result}

dir=/home/szm/auto_asr
ssh root@10.10.10.151  "
	cd ${dir};
	./run.sh test.txt test.txt test_wav 
	
" 
scp -r root@10.10.10.151:${dir}/${result}  ./

echo "successed!"


