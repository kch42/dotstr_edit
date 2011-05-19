#!/usr/bin/env bash

for locale_dir in locale/*; do
	for pofile in $locale_dir/LC_MESSAGES/*.po; do
		mofile=`echo $pofile | sed -n "s/\\.po/\\.mo/p"`;	
		echo "$pofile => $mofile";
		msgfmt "$pofile" -o "$mofile";
	done;
done;
