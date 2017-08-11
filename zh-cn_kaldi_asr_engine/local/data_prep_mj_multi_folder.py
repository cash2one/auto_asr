# -*- coding: utf-8 -*-

import sys
import os
import re

def main(input_data_dir,output_dir):
    
    ### make dir
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    ### create wav.scp
    cmd = 'find %s -iname "*.wav" &> %s/all_wav_raw.lst' % (input_data_dir,output_dir)
    os.system(cmd)
    
    cmd = 'sort -u %s/all_wav_raw.lst &> %s/all_wav.lst' % (output_dir,output_dir)
    os.system(cmd)  

    fpw = open('%s/wav.scp'%output_dir,'w')
    
    all_wav_name = []

    for non_line in open('%s/all_wav.lst'%output_dir).xreadlines():
        non_line = non_line.strip()
        if not non_line:
            continue
        wav_name = non_line.split('/')[-1][:-4]
        all_wav_name.append(wav_name)

        fpw.write(wav_name + ' ' + non_line + '\n')

    fpw.close()
    
    ### create spk2utt and utt2spk
    fpw_spk2utt = open('%s/spk2utt'%output_dir,'w')
    fpw_utt2spk = open('%s/utt2spk'%output_dir,'w')

    for all_wav_name_item in all_wav_name:
        folder_name = all_wav_name_item.replace('-0000','')
        fpw_spk2utt.write(folder_name + ' ' + all_wav_name_item + '\n')
        fpw_utt2spk.write(all_wav_name_item + ' ' + folder_name + '\n')

    fpw_spk2utt.close()
    fpw_utt2spk.close()
    
    
if __name__ == '__main__':
    
    if len(sys.argv) != 3:
	print 'python %s input_data_dir output_dir' % sys.argv[0]
    else:
	main(sys.argv[1],sys.argv[2])    


