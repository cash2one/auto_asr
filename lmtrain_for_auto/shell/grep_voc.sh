#/bin/sh -x 
dir=$1
file=$2
ls -1 $dir|while read line
do
	#echo "$dir/$line"
	cat $file|while read line_2
	do
		ret=`grep $line_2 $dir/$line`
		if ["$ret" != ""]
		then
			echo "$line_2"
		fi
	done
done 
