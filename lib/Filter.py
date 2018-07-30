#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

#from collections import Counter
#from sklearn.feature_extraction.text import CountVectorizer
#from nltk.corpus import stopwords
#from nltk.tokenize import word_tokenize
#from textblob import TextBlob
#import pandas as pd
import os 
import shutil
import sys
import glob
import string
import Settings 
from os import listdir
from os.path import isfile, join 

import configparser

Min_Occurences = 12

def Filter(config_file):
	setupDirs(config_file)
	makeDirs()
	Parse_lib = getLib()
	if Parse_lib != 'PyPDF2':
		setupDataSet()
	files = getFiles(Unfiltered_dir + '/*')
	terms = [t.replace('*', '').lower() for t in readTerms()]
	for file in files:
		text = cleanText(getText(file, lib))
		if Parse_lib =='PyPDF2':
			simple_analysis(file, text)
		else:
			pass
			#full_analysis(file, text)

def getText(file, lib):
	if lib == 'Textract':
		import textract
		return textract.process(file)
	elif lib == 'Tika':
		from tika import parser
		return parser.from_file(file)['content']
	else:
		import PyPDF2
		with open(file, 'rb') as f:
			pdfReader = PyPDF2.PdfFileReader(f)
			return ("".join(pages.append(pdfReader.getPage(page).extractText()) for page in range(0, pdfReader.getNumPages())))

def cleanText(text):
	#strip,  convert to lower, removes punctuation, removes non ascii text, removes stop words, spelling corrections
	#TODO: remove unique and uncommon words, maybe remove corrections
	stop = stopwords.words('english')
	filtered = str(text).lower().replace('[^\w\s]','').replace('\n', ' ')
	filtered = ''.join(x for x in filtered if x in string.printable)
	filtered = ' '.join(word for word in filtered.split() if not word in stop)
	#filtered = str(TextBlob(filtered).correct())
	return filtered

def simple_anaylsis(file, text):
	if sum(text.count(term) for term in terms) > 26:
		dest = Filtered_dir + '/hit/' + file.split('/')[-1] 
	else:
		dest = Filtered_dir + '/miss/' + file.split('/')[-1] 
	move_file(file, dest)

def full_analysis(file, text, dictionary, tf_idf):
	pass
	# doc = [words for words in word_tokenize(text)]
	# query_doc = dictionary.doc2bow(query_doc)
	# query_doc_tf_idf = tf_idf[query_doc]
	# print(query_doc)
	# print(query_doc_tf_idf)
	# print(sims[query_doc_tf_idf])

def setupDataSet():
	pass
	# global dictionary, tf_idf, sims
	# files = getFiles(Dataset_dir + '/*')
	# docs = [cleanText(getText(f)) for f in files]
	# tokens = [[word for word in word_tokenize(text)] for text in docs]
	# dictionary = gensim.corpora.Dictionary(gen_docs)
	# corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
	# tf_idf = gensim.models.TfidModel(corpus)
	# sims = gensim.similarities.Similarity('/usr/workdir/',tf_idf[corpus], num_features=len(dictionary))
	# print(sims)
	# print((type(sims)))

def readTerms():
	with open(Terms_file, 'r') as f:
		terms = [x.strip() for x in f.readlines()]
	return terms

def getFiles(directory):
	return glob.glob(directory)

def move_file(src, dest):
	os.rename(src, dest)

def makeDirs():
	[os.makedirs(directory) for directory in [Base_dir, Filtered_dir, Filtered_dir + '/miss', Filtered_dir + '/hit', Unfiltered_dir, Dataset_dir,Config_dir] if not os.path.exists(directory)]

def setupDirs():
	global DBase_dir, CBase_dir, Filtered_dir, Unfiltered, Dataset_dir, Word_file
	config = configparser.ConfigParser()
	config.read(Config_file)
	DBase_dir = config.get('Dirs', 'DBase_dir').replace('\'', '')
	CBase_dir = config.get('Dirs', 'Config_dir').replace('\'', '')
	Filtered_dir = DBase_dir + '/filtered/'
	Unfiltered_dir = DBase_dir + '/unfiltered/pdf'
	Dataset_dir = DBase_dir + '/dataset'

	Word_file = CSearch_dir + '/words.txt'

def getLib():
	try:
		import textract
		return 'Textract'
	except:
		print('Error Importing Textract, trying tika')
		try:
			from tika import parser
			return 'Tika'
		except:
			print('Error Importing Tika, trying PyPDF2')
			try:
				import PyPDF2
				return 'PyPDF2'
			except:
				print('Error Importing PyPDF2, exiting')
				sys.exit(0)

if __name__== "__main__":
	filter()

