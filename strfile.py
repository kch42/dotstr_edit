#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re

lotr_str_regex = re.compile(r'(.*?\:.*?)\"(.*?)\"(?:.*?)END',re.DOTALL)

def dict_parse(rawdata):
	global lotr_str_regex
	rawdata = rawdata.decode("latin-1")
	
	dictionary = {}
	
	for match, string in lotr_str_regex.findall(rawdata):
		match = match.strip()
		string = string.strip()
		
		dictionary[match] = string
	return dictionary

def dict_gen(dictionary, fp):
	for match in dictionary:
		fp.write("%s\n\"%s\"\nEND\n\n" % (match.encode('latin-1'),
		                              dictionary[match].encode('latin-1')))

def escape(text):
	return text.replace("\n", "\\n")

def unescape(text):
	return text.replace("\\n", "\n")
