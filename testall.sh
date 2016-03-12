#!/bin/bash

set -e

space_regex='[[:space:]]'

locate "*.pdf" | while read pdf
do
	if [ ! -f "$pdf" ]
	then
		echo skipping "$pdf" it is not really there
		continue
	fi
    b=$(basename "$pdf")
    if [ "$b" = "pgf_mixedmode.pdf" ]
    then
        continue
    fi
    if [ "$b" = "pgf_rcupdate1.pdf" ]
    then
        continue
    fi
	fs=$(ls -al "$pdf" | awk '{print $5}')
	if (( fs > 25000 ))
	then
		echo skipping "$pdf"
		continue
	fi
	if [[ "$pdf" =~ $space_regex ]]
	then
		echo skipping "$pdf"
		continue
	fi
	printf "%s\t%s\n" "$fs" "\"$pdf\""
	spdfinfo -i "$pdf"
done
