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
from time import sleep
from tqdm import tqdm
from os import listdir
from os.path import isfile, join 
from nltk.corpus import stopwords
from collections import Counter
from multiprocessing import Pool

import Helper

SA_count = 32
class Filterer(object):
	def __init__(self, Working_dir, config, F_count):
		os.chdir(Working_dir)
		self.DBase_dir, self.CBase_dir, self.Dataset_dir, self.Filtered_dir, self.Hit_dir, self.Miss_dir, self.Error_dir, self.Unfiltered_dir, self.App_dir, self.Misc_dir, self.CSearch_dir, self.Words_file,  = [''] * 12
		self.Config_file = config
		self.setupDirs()
		self.Files = Helper.getFiles(self.Unfiltered_dir + '/*')
		self.Fbar = tqdm(total=len(self.Files))	
		self.F_count = F_count
		self.Parse_lib = self.getLib()

	def start(self):
		self.Filter()
		# run = True
		# while run:
		# 	Files = Helper.getFiles(self.Unfiltered_dir + '/*')
		# 	self.Filter(Files)
		# 	checkFiles = Helper.getFiles(self.Unfiltered_dir + '/*')
		# 	if Files == checkFiles:
		# 		count = 0
		# 		while Files == checkFiles and count < 10:
		# 			sleep(60)
		# 			count +=1
		# 		if Files != checkFiles:
		# 			Files = checkFiles
		# 		else:
		# 			run = False
		# 	else:
		# 		Files = checkFiles

	def Filter(self):
		tqdm.write('Sorting files')
		pool = Pool(self.F_count)
		for file in self.Files:
			try:
				pool.apply_async(self.FilterWorker, args=(file,), callback=self.showProg)
			except Exception:
				logging.exception("f(%r) failed" % (args,))

			#self.FilterWorker(file)
		pool.close()
		pool.join()

	def showProg(self, *a):
	 	#self.Fbar.update()
	 	pass

	def FilterWorker(self, file):
		text = self.cleanText(self.getText(file, self.Parse_lib))
		if text == 'Error':
			self.moveFile(file, Error_dir + '/' + file.split('/')[:-1])
		else:
			self.simple_analysis(file, text)
		# elif Parse_lib =='PyPDF2':
		# 	simple_analysis(file, text)
		# else:
		# 	#full_analysis(file, text)

	def getText(self, file, lib):
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

	def cleanText(self, text):
		#strip,  convert to lower, removes punctuation, removes non ascii text, removes stop words, spelling corrections
		#TODO: remove unique and uncommon words, maybe remove corrections
		stop = stopwords.words('english')
		filtered = str(text).lower().replace('[^\w\s]','').replace('\n', ' ')
		filtered = ''.join(x for x in filtered if x in string.printable)
		filtered = ' '.join(word for word in filtered.split() if not word in stop)
		count = Counter(filtered).most_common(10)
		#filtered = str(TextBlob(filtered).correct())
		return filtered

	def simple_analysis(self, file, text):
		terms = [t.replace('*', '').lower() for t in self.readTerms()]
		if sum(text.count(term) for term in terms) > SA_count:
			dest = self.Hit_dir + '/' + file.split('/')[-1] 
		else:
			dest = self.Miss_dir + '/' + file.split('/')[-1] 
		Helper.moveFile(file, dest)

	def full_analysis(self, file, text, dictionary, tf_idf):
		pass
		# doc = [words for words in word_tokenize(text)]
		# query_doc = dictionary.doc2bow(query_doc)
		# query_doc_tf_idf = tf_idf[query_doc]
		# print(query_doc)
		# print(query_doc_tf_idf)
		# print(sims[query_doc_tf_idf])

	def setupDataSet(self):
		pass
		# global dictionary, tf_idf, sims
		# files = Helper.getFiles(Dataset_dir + '/*')
		# docs = [cleanText(getText(f)) for f in files]
		# tokens = [[word for word in word_tokenize(text)] for text in docs]
		# dictionary = gensim.corpora.Dictionary(gen_docs)
		# corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
		# tf_idf = gensim.models.TfidModel(corpus)
		# sims = gensim.similarities.Similarity('/usr/workdir/',tf_idf[corpus], num_features=len(dictionary))
		# print(sims)
		# print((type(sims)))

	def readTerms(self):
		with open(self.Words_file, 'r') as f:
			terms = [x.strip() for x in f.readlines()]
		return terms

	def setupDirs(self):
		config = configparser.ConfigParser()
		config.read(self.Config_file)
		self.DBase_dir = config.get('Dirs', 'DBase_dir').replace('\'', '')
		self.CBase_dir = config.get('Dirs', 'Config_dir').replace('\'', '')

		self.Filtered_dir = self.DBase_dir + '/filtered'
		self.Hit_dir = self.Filtered_dir + '/hit'
		self.Miss_dir = self.Filtered_dir + '/miss'
		self.Error_dir = self.Filtered_dir + '/error'
		self.Unfiltered_dir = self.DBase_dir + '/unfiltered/app'
		self.Dataset_dir = self.DBase_dir + '/dataset'
		self.CSearch_dir = self.CBase_dir + '/search'

		self.Words_file = self.CSearch_dir + '/words.txt'
		
		dirs = [self.DBase_dir, self.CBase_dir, self.Filtered_dir, self.Hit_dir, self.Miss_dir, self.Error_dir, self.Unfiltered_dir, self.Dataset_dir, self.CSearch_dir]
		[Helper.makeFolder(folder) for folder in dirs]

	def getLib(self):
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