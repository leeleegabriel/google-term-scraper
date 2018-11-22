#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18
import string
import os
import logging
import pickle
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

import lib.Helper as Helper

os.chdir('../')


class Filterer():
	def __init__(self, logger, Sample_dir, Hit_dir, Miss_dir, Error_dir, Unfiltered_dir, Words_file):
		self.self.logger = self.logger
		self.Sample_dir = Sample_dir
		self.Hit_dir = Hit_dir
		self.Miss_dir = Miss_dir
		self.Error_dir = Error_dir
		self.Unfiltered_dir = Unfiltered_dir
		self.Words_file = Words_file
		self.aThreshhold = 0.70
		self.sThreshhold = 144

	def start(self):
		Files = Helper.getFiles(self.Unfiltered_dir + '/*')
		self.logger.info('Sorting files')
		if Files:
			if not os.listdir(self.Sample_dir):
				self.logger.info("Sample Folder empty, doing simple filtering")
				self.simpleAnalysis(Files, Helper.getText(self.Words_file))
			else:
				self.complexAnalysis(Files)
			self.logger.info('Finished filtering files')
		else:
			self.logger.info('No files to filter')

	def complexAnalysis(self, files):
		if os.path.isfile('./config/text_classifier'):
			model = self.loadDataset()
		else:
			model = self.getDataset('./config/dataset')

		for file in files:
			try:
				text = self.cleanText(self.getText(file))
				if model.predict(text) > self.aThreshhold:
					dest = self.fHit_dir + file.split('/')[-1]
				else:
					dest = self.Miss_dir + file.split('/')[-1]
				Helper.moveFile(file, dest)
			except Helper.ParseError:
				self.logger.error('Encountered Parse Error with %s', file)
				dest = self.Error_dir + file.split('/')[:-1]
			Helper.moveFile(file, dest)

	def simpleAnalysis(self, files, keywords):
		for file in files:
			try:
				text = self.getText(file)
				count = 0
				[count + 1 for word in text if text in keywords]
				if count > self.sThreshhold:
					dest = self.Hit_dir + file.split('/')[-1]
				else:
					dest = self.Miss_dir + file.split('/')[-1]
			except Helper.ParseError:
				self.logger.error('Encountered Parse Error with %s', file)
				dest = self.Error_dir + file.split('/')[:-1]
			Helper.moveFile(file, dest)

	def getText(self, file):
		try:
			import textract
			text = textract.process(file)
		except Exception:
			try:
				from tika import parser
				text = parser.from_file(file)['content']
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

	def loadDataset(self):
		with open('./config/text_classifier', 'rb') as p:
			model = pickle.load(p)
			return model

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

		with open('./config/text_classifier', 'wb') as p:
			pickle.dump(classifier,p)

		return classifier
