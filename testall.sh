#!/bin/bash

space_regex='[[:space:]]'

locate "*.pdf" | while read pdf
do
	if [ ! -f "$pdf" ]
	then
		echo skipping "$pdf" it is not really there
		continue
	fi
	fs=$(ls -al "$pdf" | awk '{print $5}')
	if (( fs > 10000 ))
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
