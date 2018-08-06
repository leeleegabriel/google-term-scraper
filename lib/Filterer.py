#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

#from sklearn.feature_extraction.text import CountVectorizer
#from nltk.tokenize import word_tokenize
#from textblob import TextBlob
#import pandas as pd
import string
import configparser
import os
from tqdm import tqdm
from os import listdir
from nltk.corpus import stopwords

import Helper

SA_count = 32

def start(Working_dir, Config_file):
	getDirs(Working_dir, Config_file)
	Filter()

def Filter():
	Files = Helper.getFiles(Unfiltered_dir + '/*')
	tqdm.write('Sorting files')
	for file in tqdm(Files, unit='Files'):
		text = cleanText(getText(file))
		if text == 'Error':
			Helper.moveFile(file, Error_dir + '/' + file.split('/')[:-1])
		else:
			dest = simple_analysis(file, text)
		Helper.moveFile(file, dest)

def getText(file, lib):
	try:
		import textract
		text =  textract.process(file)
	except KeyboardInterrupt:
		raise
	except Exception:
		try:
			from tika import parser
			text = parser.from_file(file)['content']
		except Exception:
			text = 'Error'
	return text 

def cleanText(text):
	stop = stopwords.words('english')
	filtered = str(text).lower().replace('[^\w\s]','').replace('\n', ' ')
	filtered = ''.join(x for x in filtered if x in string.printable)
	filtered = ' '.join(word for word in filtered.split() if not word in stop)
	#count = Counter(filtered).most_common(10)
	return filtered

def simple_analysis(file, text):
	terms = [t.replace('*', '').lower() for t in readTerms()]
	if sum(text.count(term) for term in terms) > SA_count:
		dest = Hit_dir + '/' + file.split('/')[-1] 
	else:
		dest = Miss_dir + '/' + file.split('/')[-1] 
	return dest

def readTerms():
	with open(Words_file, 'r') as f:
		terms = [x.strip() for x in f.readlines()]
	return terms

def getDirs(Working_dir, Config_file):
	global Hit_dir, Miss_dir, Unfiltered_dir, Error_dir, Words_file
	os.chdir(Working_dir)
	config = configparser.ConfigParser()
	config.read(Config_file)
	DBase_dir = config.get('Dirs', 'DBase_dir').replace('\'', '')
	CBase_dir = config.get('Dirs', 'Config_dir').replace('\'', '')

	Filtered_dir = DBase_dir + '/filtered'
	Hit_dir = Filtered_dir + '/hit'
	Miss_dir = Filtered_dir + '/miss'
	Error_dir = Filtered_dir + '/error'
	Unfiltered_dir = DBase_dir + '/unfiltered/app'
	CSearch_dir = CBase_dir + '/search'

	Words_file = CSearch_dir + '/words.txt'

if __name__== "__main__":
	start(os.path.abspath('..'),'./config/config.txt')