#!/usr/bin/python3
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18
import os
# import logging
# import pickle
import sys
import traceback
from time import sleep
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.model_selection import train_test_split
# from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

import lib.Helper as Helper

sys.path.append('../')


class Filterer():
	def __init__(self, logger, Scraper, Sample_dir, Hit_dir, Miss_dir, Error_dir, Unfiltered_dir, Words_file):
		self.logger = logger
		self.Scraper = Scraper
		self.Sample_dir = Sample_dir
		self.Hit_dir = Hit_dir
		self.Miss_dir = Miss_dir
		self.Error_dir = Error_dir
		self.Unfiltered_dir = Unfiltered_dir
		self.Words_file = Words_file
		self.running = True
		self.fin = False
		self.aThreshhold = 0.70
		self.sThreshhold = 144
		self.Downloader_wait = 30

	def run(self, loop):
		try:
			while self.Scraper.running and self.running:
				Files = Helper.getFiles(self.Unfiltered_dir + '/*')
				if Files:
					if not os.listdir(self.Sample_dir):
						self.simpleAnalysis(Files, Helper.getText(self.Words_file))
					else:
						self.complexAnalysis(Files)
					self.logger.info('Finished filtering files')
				else:
					self.logger.info('No files to filter')
				sleep(self.Downloader_wait)
		except Exception as e:
			self.logger.error(str(e))
			traceback.print_exc()
		self.logger.debug('Fin.')
		self.fin = True

	def complexAnalysis(self, files):
		# if os.path.isfile('./config/text_classifier'):
		# 	model = self.loadDataset()
		# else:
		self.logger.info('Sorting files: Complex')
		model = self.getDataset('./config/dataset')
		i = 0
		while self.running and i < len(files):
			f = files[i]
			try:
				text = self.cleanText(self.getText(f))
				if model.predict(text) > self.aThreshhold:
					dest = self.fHit_dir + f.split('/')[-1]
				else:
					dest = self.Miss_dir + f.split('/')[-1]
				Helper.moveFile(f, dest)
			except Helper.ParseError:
				self.logger.error('Encountered Parse Error with %s', f)
				dest = self.Error_dir + f.split('/')[:-1]
			Helper.moveFile(f, dest)
			i += 1

	def simpleAnalysis(self, files, keywords):
		self.logger.info('Sorting files: Simple')
		i = 0
		while self.running and i < len(files):
			f = files[i]
			try:
				text = self.getText(f)
				count = 0
				for word in text:
					if text in keywords:
						count += 1
				if count > self.sThreshhold:
					dest = self.Hit_dir + f.split('/')[-1]
				else:
					dest = self.Miss_dir + f.split('/')[-1]
			except Helper.ParseError:
				self.logger.error('Encountered Parse Error with %s', f)
				dest = self.Error_dir + f.split('/')[:-1]
			Helper.moveFile(f, dest)
			i += 1

	def getText(self, f):
		try:
			import textract
			text = textract.process(f)
		except Exception:
			try:
				from tika import parser
				text = parser.from_file(f)['content']
			except Exception:
				raise Helper.ParseError('Whoops')
		return text

	def cleanText(self, text):
		filtered = word_tokenize(text)#split strings into words
		filtered = [word for word in filtered if word.isalpha()]#removes all tokens that are not alphabetic

		stop = stopwords.words('english')
		filtered = [word for word in filtered if word not in stop]#removes stop words

		port = PorterStemmer()
		filtered = [port.stem(word) for word in filtered]

		return filtered

	# def loadDataset(self):
	# 	with open('./config/text_classifier', 'rb') as p:
	# 		model = pickle.load(p)
	# 		return model

	def getDataset(self):
		files = [self.Sample_dir + '/' + file for file in os.listdir(self.Sample_dir)]
		text = [self.cleanText(self.getText(files)) for file in files]

		vectorizer = CountVectorizer(max_features=1500, min_df=5, max_df=0.7, stop_words=stopwords.words('english'))
		x = vectorizer.fit_transform(text).toarray()

		tfidfconverter = TfidfTransformer()
		y = tfidfconverter.fit_transform(x).toarray() ## x or y?

		x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)

		classifier = RandomForestClassifier(n_estimators=1000, random_state=0) 
		classifier.fit(x_train, y_train)

		y_pred = classifier.predict(x_test)

		# with open('./config/text_classifier', 'wb') as p:
		# 	pickle.dump(classifier,p)

		return classifier
