#!/bin/sh

input_file=$1
rm -rf test/*
rm -rf $input_file.ok
cp -r $input_file test/

python handleCorpus.py test dict/ChineseChDict.dict

mv test/$input_file.ok ./

