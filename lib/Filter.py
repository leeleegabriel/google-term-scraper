#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

#from sklearn.feature_extraction.text import CountVectorizer
#from nltk.tokenize import word_tokenize
#from textblob import TextBlob
#import pandas as pd
import os 
import shutil
import sys
import string
import Settings 
import configparser
from tqdm import tqdm
from os import listdir
from os.path import isfile, join 
from nltk.corpus import stopwords
from collections import Counter

import FileIO

SA_count = 32

def start(WD, config):
	Filter(WD, config)

def Filter(Working_dir, config_file):
	setupDirs(Working_dir, config_file)
	Parse_lib = getLib()
	if Parse_lib != 'PyPDF2':
		setupDataSet()
	files = FileIO.getFiles(Unfiltered_dir + '/*')
	tqdm.write('Sorting files')
	for file in tqdm(files):
		Parse_lib = 'Textract'
		text = cleanText(getText(file, Parse_lib))
		Parse_lib = 'PyPDF2'
		if text == 'Error':
			tqdm.write('Error with File : %s' % file)
			moveFile(file, Error_dir + '/' + file.split('/')[:-1])
		elif Parse_lib =='PyPDF2':
			simple_analysis(file, text)
		else:
			pass
			#full_analysis(file, text)

def getText(file, lib):
	tqdm.write(file)
	try:
		if lib == 'Textract':
			import textract
			text =  textract.process(file)
		elif lib == 'Tika':
			from tika import parser
			text = parser.from_file(file)['content']
		else:
			import PyPDF2
			with open(file, 'rb') as f:
				pdfReader = PyPDF2.PdfFileReader(f)
				text =(" ".join(pdfReader.getPage(page).extractText()) for page in range(0, pdfReader.getNumPages()))
	except Exception as e:
		text = 'Error'
	return text 

def cleanText(text):
	#strip,  convert to lower, removes punctuation, removes non ascii text, removes stop words, spelling corrections
	#TODO: remove unique and uncommon words, maybe remove corrections
	stop = stopwords.words('english')
	filtered = str(text).lower().replace('[^\w\s]','').replace('\n', ' ')
	filtered = ''.join(x for x in filtered if x in string.printable)
	filtered = ' '.join(word for word in filtered.split() if not word in stop)
	count = Counter(filtered).most_common(10)
	#filtered = str(TextBlob(filtered).correct())
	return filtered

def simple_analysis(file, text):
	terms = [t.replace('*', '').lower() for t in readTerms()]
	if sum(text.count(term) for term in terms) > SA_count:
		dest = Hit_dir + '/' + file.split('/')[-1] 
	else:
		dest = Miss_dir + '/' + file.split('/')[-1] 
	FileIO.moveFile(file, dest)

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
	# files = FileIO.getFiles(Dataset_dir + '/*')
	# docs = [cleanText(getText(f)) for f in files]
	# tokens = [[word for word in word_tokenize(text)] for text in docs]
	# dictionary = gensim.corpora.Dictionary(gen_docs)
	# corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
	# tf_idf = gensim.models.TfidModel(corpus)
	# sims = gensim.similarities.Similarity('/usr/workdir/',tf_idf[corpus], num_features=len(dictionary))
	# print(sims)
	# print((type(sims)))

def readTerms():
	with open(Words_file, 'r') as f:
		terms = [x.strip() for x in f.readlines()]
	return terms

def setupDirs(Working_dir, Config_file):
	global DBase_dir, CBase_dir, Filtered_dir, Hit_dir, Miss_dir, Unfiltered_dir, Dataset_dir, Words_file
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
	Dataset_dir = DBase_dir + '/dataset'
	CSearch_dir = CBase_dir + '/search'

	Words_file = CSearch_dir + '/words.txt'
	
	[FileIO.makeFolder(folder) for folder in [DBase_dir, CBase_dir, Filtered_dir, Hit_dir, Miss_dir, Error_dir, Unfiltered_dir, Dataset_dir, CSearch_dir]]

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
	Filter(os.path.abspath('..'),'./config/config.txt')