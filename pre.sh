#!/bin/sh

if(($#<1))
then
	echo "usage: $0 utf16_file \n"
	exit 0
fi

iconv -f utf-16 -t utf-8 $1 > $1.utf8 
awk -F"\t" '{if(NR%2==1){print $1".wav:"$2}}' $1.utf8 > $1.utf8.lab
awk -F":" '{print $2}' $1.utf8.lab > $1.utf8.lab.train
