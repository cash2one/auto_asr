#/bin/sh -x 

in_dir=$1
out_dir=$2
mkdir -p $out_dir

ls -1 $in_dir|while read line
do
	./bin/generate_voc $in_dir/$line $out_dir/$line.voc 0 > generate.log 
done
